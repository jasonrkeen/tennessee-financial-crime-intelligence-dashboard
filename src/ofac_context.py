from pathlib import Path

import pandas as pd
import requests

from src.config import (
    OFAC_CONSOLIDATED_ADDRESS_URL,
    OFAC_CONSOLIDATED_PRIMARY_URL,
    OFAC_CONTEXT_FLAGS_FILE,
    OFAC_CONTEXT_SUMMARY_FILE,
    OFAC_DOWNLOAD_DIR,
    OFAC_SDN_ADDRESS_URL,
    OFAC_SDN_PRIMARY_URL,
    OFAC_TENNESSEE_MATCHES_FILE,
)


# ------------------------------------------------------------
# Tennessee geography matching
# ------------------------------------------------------------

TENNESSEE_CITY_COUNTY_TERMS = [
    "nashville",
    "memphis",
    "knoxville",
    "chattanooga",
    "clarksville",
    "murfreesboro",
    "franklin",
    "johnson city",
    "jackson",
    "bartlett",
    "hendersonville",
    "kingsport",
    "collierville",
    "cleveland",
    "brentwood",
    "gallatin",
    "sumner",
    "sumner county",
    "davidson county",
    "shelby county",
    "knox county",
    "hamilton county",
    "rutherford county",
    "williamson county",
    "montgomery county",
    "wilson county",
    "maury county",
    "madison county",
    "sevier county",
    "oak ridge",
    "mount juliet",
    "mt juliet",
    "smyrna",
    "spring hill",
    "cookeville",
    "bristol",
    "columbia",
    "la vergne",
    "maryville",
    "morristown",
    "tullahoma",
    "dyersburg",
]

# Terms that are too ambiguous globally unless there is explicit Tennessee
# or a clear United States country signal.
AMBIGUOUS_TENNESSEE_PLACE_TERMS = [
    "lebanon",
    "paris",
    "bristol",
    "columbia",
    "cleveland",
    "franklin",
    "jackson",
]

US_COUNTRY_TERMS = {
    "united states",
    "united states of america",
    "usa",
    "u.s.a",
    "u.s.",
    "us",
}


SDN_PRIMARY_COLUMNS = [
    "ent_num",
    "sdn_name",
    "sdn_type",
    "program",
    "title",
    "call_sign",
    "vess_type",
    "tonnage",
    "grt",
    "vess_flag",
    "vess_owner",
    "remarks",
]

SDN_ADDRESS_COLUMNS = [
    "ent_num",
    "add_num",
    "address",
    "city_state_postal",
    "country",
    "add_remarks",
]

CONSOLIDATED_PRIMARY_COLUMNS = [
    "ent_num",
    "sdn_name",
    "sdn_type",
    "program",
    "title",
    "call_sign",
    "vess_type",
    "tonnage",
    "grt",
    "vess_flag",
    "vess_owner",
    "remarks",
]

CONSOLIDATED_ADDRESS_COLUMNS = [
    "ent_num",
    "add_num",
    "address",
    "city_state_postal",
    "country",
    "add_remarks",
]


def download_file(url: str, output_path: Path, overwrite: bool = False) -> Path:
    """
    Download an OFAC CSV file.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not overwrite:
        print(f"Already exists: {output_path}")
        return output_path

    print(f"Downloading OFAC file: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 Tennessee Financial Crime Intelligence Dashboard "
            "research script"
        )
    }

    response = requests.get(url, headers=headers, timeout=90)
    response.raise_for_status()

    output_path.write_bytes(response.content)

    print(f"Saved OFAC file: {output_path}")
    return output_path


def download_ofac_files(overwrite: bool = False) -> dict[str, Path]:
    """
    Download OFAC SDN and consolidated CSV files.
    """

    files = {
        "sdn_primary": OFAC_DOWNLOAD_DIR / "sdn.csv",
        "sdn_address": OFAC_DOWNLOAD_DIR / "add.csv",
        "consolidated_primary": OFAC_DOWNLOAD_DIR / "cons_prim.csv",
        "consolidated_address": OFAC_DOWNLOAD_DIR / "cons_add.csv",
    }

    url_map = {
        "sdn_primary": OFAC_SDN_PRIMARY_URL,
        "sdn_address": OFAC_SDN_ADDRESS_URL,
        "consolidated_primary": OFAC_CONSOLIDATED_PRIMARY_URL,
        "consolidated_address": OFAC_CONSOLIDATED_ADDRESS_URL,
    }

    for key, path in files.items():
        try:
            download_file(url_map[key], path, overwrite=overwrite)
        except Exception as exc:
            print(f"WARNING: Could not download {key}: {exc}")

    return files


def read_ofac_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    """
    Read an OFAC legacy CSV file without headers.
    """

    if not path.exists():
        return pd.DataFrame(columns=columns)

    encodings = ["utf-8", "utf-8-sig", "latin1"]

    for encoding in encodings:
        try:
            df = pd.read_csv(
                path,
                header=None,
                names=columns,
                dtype=str,
                encoding=encoding,
                on_bad_lines="skip",
            )
            return df.fillna("")
        except UnicodeDecodeError:
            continue

    return pd.read_csv(
        path,
        header=None,
        names=columns,
        dtype=str,
        encoding="latin1",
        on_bad_lines="skip",
    ).fillna("")


def build_address_text(row: pd.Series) -> str:
    """
    Build a searchable address string.
    """

    parts = [
        row.get("address", ""),
        row.get("city_state_postal", ""),
        row.get("country", ""),
        row.get("add_remarks", ""),
    ]

    return " ".join(str(part) for part in parts if str(part).strip()).lower()


def tokenize_address_text(text: str) -> list[str]:
    """
    Tokenize address text for safer matching.
    """

    clean = (
        str(text)
        .lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace(";", " ")
        .replace(":", " ")
        .replace("/", " ")
        .replace("\\", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("-", " ")
        .replace("[", " ")
        .replace("]", " ")
    )

    return clean.split()


def has_us_country_signal(row: pd.Series) -> bool:
    """
    Return True if the OFAC address row has a clear United States signal.

    This prevents false positives from non-U.S. addresses where 'TN' appears
    as a street abbreviation or local term, such as Tallinn street names.
    """

    country = str(row.get("country", "")).strip().lower()
    text = build_address_text(row)
    tokens = tokenize_address_text(text)

    if country in US_COUNTRY_TERMS:
        return True

    if "united states" in text or "united states of america" in text:
        return True

    if "usa" in tokens:
        return True

    # Require 'us' as a standalone token, not part of a longer word.
    if "us" in tokens:
        return True

    return False


def has_state_signal(row: pd.Series) -> tuple[bool, list[str], str]:
    """
    Detect explicit Tennessee state signals.

    Important:
    - 'tennessee' is accepted as an explicit state signal.
    - 'tn' is accepted only when there is a clear U.S. country signal.
      This avoids false positives from foreign street abbreviations such as
      Tallinn 'Tn' street-name usage.
    """

    text = build_address_text(row)
    tokens = tokenize_address_text(text)
    us_signal = has_us_country_signal(row)

    matched = []

    if "tennessee" in text:
        matched.append("tennessee")
        return True, matched, "accepted_explicit_tennessee_signal"

    if "tn" in tokens:
        matched.append("tn")

        if us_signal:
            return True, matched, "accepted_tn_with_us_country_signal"

        return False, matched, "rejected_tn_without_us_country_signal"

    return False, [], "no_state_signal"


def find_city_county_matches(row: pd.Series) -> list[str]:
    """
    Find Tennessee city/county terms in the address text.
    """

    text = build_address_text(row)
    matches = []

    for term in TENNESSEE_CITY_COUNTY_TERMS:
        if term in text:
            matches.append(term)

    return sorted(set(matches))


def tennessee_match_details(row: pd.Series) -> tuple[str, str, str]:
    """
    Return matched Tennessee terms, match level, and match quality.

    Rules:
    - Explicit 'tennessee' is accepted as a state-level match.
    - 'tn' is accepted only if there is a clear U.S. country signal.
    - City/county terms are accepted only if there is also a clear U.S. country signal.
    - Ambiguous place names are rejected unless stronger geography support exists.
    """

    state_match, state_terms, state_quality = has_state_signal(row)

    if state_match:
        city_matches = find_city_county_matches(row)
        matched_terms = sorted(set(state_terms + city_matches))
        return ", ".join(matched_terms), "state", state_quality

    # If 'tn' appeared but lacked U.S. support, reject immediately and document why.
    if state_terms and state_quality == "rejected_tn_without_us_country_signal":
        return ", ".join(state_terms), "rejected_state_abbreviation", state_quality

    city_matches = find_city_county_matches(row)

    if not city_matches:
        return "", "", "no_tennessee_indicator"

    us_signal = has_us_country_signal(row)

    if not us_signal:
        return (
            ", ".join(city_matches),
            "rejected_city_or_county",
            "rejected_no_us_or_state_signal",
        )

    ambiguous_matches = [
        term for term in city_matches if term in AMBIGUOUS_TENNESSEE_PLACE_TERMS
    ]

    if ambiguous_matches and len(city_matches) == len(ambiguous_matches):
        return (
            ", ".join(city_matches),
            "rejected_ambiguous_city",
            "rejected_ambiguous_city_without_state_signal",
        )

    return ", ".join(city_matches), "city_or_county", "accepted_us_city_county_signal"


def add_tennessee_match_fields(address: pd.DataFrame) -> pd.DataFrame:
    """
    Add Tennessee match fields to an address dataframe.
    """

    if address.empty:
        address["match_reason"] = ""
        address["match_level"] = ""
        address["match_quality"] = ""
        return address

    details = address.apply(tennessee_match_details, axis=1)

    address["match_reason"] = [item[0] for item in details]
    address["match_level"] = [item[1] for item in details]
    address["match_quality"] = [item[2] for item in details]

    return address


def parse_ofac_list(
    list_type: str,
    primary_path: Path,
    address_path: Path,
    primary_columns: list[str],
    address_columns: list[str],
    source_url: str,
) -> pd.DataFrame:
    """
    Parse one OFAC list and return accepted Tennessee address matches.
    """

    primary = read_ofac_csv(primary_path, primary_columns)
    address = read_ofac_csv(address_path, address_columns)

    if primary.empty or address.empty:
        return pd.DataFrame()

    primary["ent_num"] = primary["ent_num"].astype(str)
    address["ent_num"] = address["ent_num"].astype(str)

    address = add_tennessee_match_fields(address)

    accepted_levels = {"state", "city_or_county"}
    matches = address[address["match_level"].isin(accepted_levels)].copy()

    if matches.empty:
        return pd.DataFrame()

    merged = matches.merge(
        primary[
            [
                "ent_num",
                "sdn_name",
                "sdn_type",
                "program",
                "remarks",
            ]
        ],
        on="ent_num",
        how="left",
    )

    merged["list_type"] = list_type
    merged["source_url"] = source_url

    output_cols = [
        "list_type",
        "ent_num",
        "sdn_name",
        "sdn_type",
        "program",
        "address",
        "city_state_postal",
        "country",
        "add_remarks",
        "match_reason",
        "match_level",
        "match_quality",
        "remarks",
        "source_url",
    ]

    return merged[output_cols].copy()


def build_ofac_tennessee_matches() -> pd.DataFrame:
    """
    Build accepted Tennessee-related OFAC address matches.
    """

    download_paths = download_ofac_files(overwrite=False)

    frames = []

    sdn_matches = parse_ofac_list(
        list_type="SDN",
        primary_path=download_paths["sdn_primary"],
        address_path=download_paths["sdn_address"],
        primary_columns=SDN_PRIMARY_COLUMNS,
        address_columns=SDN_ADDRESS_COLUMNS,
        source_url=OFAC_SDN_ADDRESS_URL,
    )

    if not sdn_matches.empty:
        frames.append(sdn_matches)

    cons_matches = parse_ofac_list(
        list_type="Consolidated Non-SDN",
        primary_path=download_paths["consolidated_primary"],
        address_path=download_paths["consolidated_address"],
        primary_columns=CONSOLIDATED_PRIMARY_COLUMNS,
        address_columns=CONSOLIDATED_ADDRESS_COLUMNS,
        source_url=OFAC_CONSOLIDATED_ADDRESS_URL,
    )

    if not cons_matches.empty:
        frames.append(cons_matches)

    output_columns = [
        "list_type",
        "ent_num",
        "sdn_name",
        "sdn_type",
        "program",
        "address",
        "city_state_postal",
        "country",
        "add_remarks",
        "match_reason",
        "match_level",
        "match_quality",
        "remarks",
        "source_url",
    ]

    if not frames:
        matches = pd.DataFrame(columns=output_columns)
    else:
        matches = pd.concat(frames, ignore_index=True)
        matches = matches.drop_duplicates()
        matches = matches.sort_values(["list_type", "program", "sdn_name"])

    matches.to_csv(OFAC_TENNESSEE_MATCHES_FILE, index=False)

    print(f"OFAC Tennessee address matches saved to: {OFAC_TENNESSEE_MATCHES_FILE}")
    print(f"Accepted OFAC Tennessee matches: {len(matches):,.0f}")

    return matches


def summarize_ofac_context(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize accepted OFAC Tennessee address matches.
    """

    if matches.empty:
        summary = pd.DataFrame(
            [
                {
                    "metric": "Tennessee OFAC address matches",
                    "value": 0,
                    "interpretation": (
                        "No accepted Tennessee-related address indicators were found in the downloaded "
                        "OFAC SDN or consolidated address files after requiring explicit Tennessee, "
                        "TN with U.S. country validation, or U.S.-anchored city/county matching."
                    ),
                    "methodology_note": (
                        "OFAC geography screening is context only and does not indicate SAR activity, "
                        "local criminal activity, or enforcement action."
                    ),
                }
            ]
        )

        summary.to_csv(OFAC_CONTEXT_SUMMARY_FILE, index=False)
        print(f"OFAC context summary saved to: {OFAC_CONTEXT_SUMMARY_FILE}")

        return summary

    rows = []

    rows.append(
        {
            "metric": "Tennessee OFAC address matches",
            "value": len(matches),
            "interpretation": (
                "Number of accepted OFAC address records containing Tennessee-related indicators "
                "after stricter state/U.S. geography validation."
            ),
            "methodology_note": (
                "Accepted matches require explicit Tennessee, TN with a clear U.S. country signal, "
                "or a Tennessee city/county term with a clear U.S. country signal."
            ),
        }
    )

    rows.append(
        {
            "metric": "Unique listed parties with Tennessee address indicators",
            "value": matches["ent_num"].nunique(),
            "interpretation": (
                "Number of unique OFAC listed parties with at least one accepted Tennessee-related "
                "address indicator."
            ),
            "methodology_note": (
                "This is sanctions-screening geography context only, not evidence of Tennessee SAR activity."
            ),
        }
    )

    for list_type, group in matches.groupby("list_type"):
        rows.append(
            {
                "metric": f"{list_type} Tennessee address matches",
                "value": len(group),
                "interpretation": (
                    f"Number of accepted Tennessee-related address records from the {list_type} list."
                ),
                "methodology_note": "List-level count from accepted OFAC address matches.",
            }
        )

    if "match_level" in matches.columns:
        for match_level, group in matches.groupby("match_level"):
            if str(match_level).strip():
                rows.append(
                    {
                        "metric": f"Match level: {match_level}",
                        "value": len(group),
                        "interpretation": (
                            "Count of accepted Tennessee-related OFAC address records by match type."
                        ),
                        "methodology_note": (
                            "State-level matches require explicit Tennessee or TN with a U.S. country signal. "
                            "City/county matches require a clear U.S. country signal."
                        ),
                    }
                )

    if "match_quality" in matches.columns:
        for match_quality, group in matches.groupby("match_quality"):
            if str(match_quality).strip():
                rows.append(
                    {
                        "metric": f"Match quality: {match_quality}",
                        "value": len(group),
                        "interpretation": (
                            "Count of accepted Tennessee-related OFAC address records by validation rule."
                        ),
                        "methodology_note": "Used to document why each geography match was accepted.",
                    }
                )

    for program, group in matches.groupby("program"):
        if pd.isna(program) or str(program).strip() == "":
            continue

        rows.append(
            {
                "metric": f"Program: {program}",
                "value": len(group),
                "interpretation": (
                    "OFAC sanctions program represented among accepted Tennessee-related address matches."
                ),
                "methodology_note": (
                    "Program counts are descriptive context and should not be interpreted as Tennessee SAR activity."
                ),
            }
        )

    summary = pd.DataFrame(rows).sort_values("value", ascending=False)

    summary.to_csv(OFAC_CONTEXT_SUMMARY_FILE, index=False)
    print(f"OFAC context summary saved to: {OFAC_CONTEXT_SUMMARY_FILE}")

    return summary


def build_ofac_context_flags(matches: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """
    Build OFAC context flags.
    """

    flags = []

    if matches.empty:
        flags.append(
            {
                "flag_type": "OFAC Tennessee Address Context",
                "severity": "Informational",
                "description": (
                    "No accepted Tennessee-related address indicators were identified in the downloaded "
                    "OFAC files after stricter geography validation. TN-only matches without U.S. country "
                    "support are rejected to avoid foreign street-abbreviation false positives."
                ),
                "methodology_scope": "Supporting sanctions-screening context",
            }
        )
    else:
        unique_parties = matches["ent_num"].nunique()

        state_matches = 0
        city_county_matches = 0

        if "match_level" in matches.columns:
            state_matches = len(matches[matches["match_level"].eq("state")])
            city_county_matches = len(matches[matches["match_level"].eq("city_or_county")])

        flags.append(
            {
                "flag_type": "OFAC Tennessee Address Context",
                "severity": "Informational",
                "description": (
                    f"OFAC list data includes {len(matches):,.0f} accepted Tennessee-related "
                    f"address records and {unique_parties:,.0f} unique listed parties after stricter "
                    f"geography validation. State-level matches: {state_matches:,.0f}; "
                    f"U.S.-anchored city/county matches: {city_county_matches:,.0f}."
                ),
                "methodology_scope": "Supporting sanctions-screening context",
            }
        )

        top_programs = (
            matches.groupby("program", as_index=False)
            .size()
            .sort_values("size", ascending=False)
            .head(5)
        )

        for _, row in top_programs.iterrows():
            program = row.get("program", "Unknown")
            count = row.get("size", 0)

            flags.append(
                {
                    "flag_type": "OFAC Program Context",
                    "severity": "Informational",
                    "description": (
                        f"OFAC program {program} appears in {count:,.0f} accepted "
                        "Tennessee-related address records."
                    ),
                    "methodology_scope": "Supporting sanctions-screening context",
                }
            )

    flags.append(
        {
            "flag_type": "Methodology Limitation",
            "severity": "Informational",
            "description": (
                "OFAC address matches do not indicate confirmed local criminal activity, SAR filings, "
                "or Tennessee enforcement action; they support sanctions-screening geographic context only."
            ),
            "methodology_scope": "Methodology limitation",
        }
    )

    flags_df = pd.DataFrame(flags)
    flags_df.to_csv(OFAC_CONTEXT_FLAGS_FILE, index=False)

    print(f"OFAC context flags saved to: {OFAC_CONTEXT_FLAGS_FILE}")

    return flags_df


def run_ofac_context_analysis() -> dict:
    """
    Run OFAC sanctions geography context analysis.
    """

    matches = build_ofac_tennessee_matches()
    summary = summarize_ofac_context(matches)
    flags = build_ofac_context_flags(matches, summary)

    return {
        "ofac_matches": matches,
        "ofac_summary": summary,
        "ofac_flags": flags,
    }