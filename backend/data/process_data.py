"""
Data Processing Script
Reads all JoSAA Excel files, cleans and normalizes data,
and outputs a combined JSON file for the backend.
"""

import pandas as pd
import json
import os
import re

# ─── Branch Normalization Map ───────────────────────────────────────────────
# Maps variant program names to a standard short name
BRANCH_NORMALIZE = {
    "Computer Science and Engineering": "CSE",
    "Computer Science": "CSE",
    "Computer Engineering": "CSE",
    "Computer Science and Engineering (Artificial Intelligence and Machine Learning)": "CSE (AI/ML)",
    "Computer Science and Engineering (Artificial Intelligence)": "CSE (AI)",
    "Artificial Intelligence and Data Science": "AI & DS",
    "Artificial Intelligence": "AI",
    "Computer Science and Engineering (Data Science)": "CSE (DS)",
    "Computer Science and Engineering (Cyber Security)": "CSE (Cyber)",
    "Computer Science and Engineering (Internet of Things)": "CSE (IoT)",
    "Data Science and Engineering": "Data Science",
    "Data Science and Artificial Intelligence": "Data Science & AI",
    "Information Technology": "IT",
    "Information Science and Engineering": "IT",
    "Mathematics and Computing": "Mathematics & Computing",
    "B.Tech in Mathematics and Computing": "Mathematics & Computing",
    "Mathematics and Data Science": "Mathematics & Computing",
    "Electronics and Communication Engineering": "ECE",
    "Electronics and Communication": "ECE",
    "Electronics & Communication Engineering": "ECE",
    "Electronics and Telecommunication Engineering": "ECE",
    "Electronics and Instrumentation Engineering": "EI",
    "Electronics Engineering": "ECE",
    "Electronics Engineering (VLSI Design and Technology)": "ECE (VLSI)",
    "B.Tech in Microelectronics & VLSI": "ECE (VLSI)",
    "Electrical Engineering": "EE",
    "Electrical and Electronics Engineering": "EEE",
    "Electrical Engineering (Power and Automation)": "EE (Power)",
    "Mechanical Engineering": "ME",
    "Mechanical Engineering (Manufacturing)": "ME (Manufacturing)",
    "Production Engineering": "Production",
    "Production and Industrial Engineering": "Production",
    "Industrial Engineering": "Industrial",
    "Industrial Engineering and Operations Research": "Industrial",
    "Manufacturing Engineering": "Manufacturing",
    "Civil Engineering": "CE",
    "Civil Engineering (Construction Technology and Management)": "CE (Construction)",
    "Chemical Engineering": "Chemical",
    "Chemical Science and Technology": "Chemical",
    "Biotechnology": "Biotech",
    "Biotechnology and Biochemical Engineering": "Biotech",
    "Bio Engineering": "Biotech",
    "Bio Medical Engineering": "Biomedical",
    "Biomedical Engineering": "Biomedical",
    "Metallurgical and Materials Engineering": "Metallurgy",
    "Metallurgical Engineering": "Metallurgy",
    "Metallurgical Engineering and Materials Science": "Metallurgy",
    "Materials Engineering": "Materials",
    "B.Tech in Materials Science and Engineering": "Materials",
    "Materials Science and Engineering": "Materials",
    "Mining Engineering": "Mining",
    "Mining and Mineral Engineering": "Mining",
    "Textile Engineering": "Textile",
    "Textile Technology": "Textile",
    "Ceramic Engineering": "Ceramic",
    "Aerospace Engineering": "Aerospace",
    "Architecture": "Architecture",
    "Planning": "Planning",
    "Engineering Physics": "Engineering Physics",
    "Physics": "Physics",
    "Chemistry": "Chemistry",
    "BS in Mathematics": "Mathematics",
    "BS in Chemical Sciences": "Chemical Sciences",
    "Economics": "Economics",
    "Environmental Science and Engineering": "Environmental",
    "Energy Engineering": "Energy",
    "Ocean Engineering and Naval Architecture": "Ocean Engineering",
    "Naval Architecture and Ocean Engineering": "Ocean Engineering",
    "Petroleum Engineering": "Petroleum",
    "Food Process Engineering": "Food Technology",
    "Food Engineering and Technology": "Food Technology",
    "Food Technology": "Food Technology",
    "Agricultural Engineering": "Agricultural",
    "Pharmaceutical Engineering and Technology": "Pharma",
    "Engineering and Computational Mechanics": "Computational Mechanics",
    "B.Tech in General Engineering": "General Engineering",
    "Smart Manufacturing": "Smart Manufacturing",
    "Mechatronics Engineering": "Mechatronics",
    "Instrumentation and Control Engineering": "Instrumentation",
}

# ─── Institute → State Mapping ──────────────────────────────────────────────
INSTITUTE_STATE = {
    # IITs
    "Indian Institute of Technology Bhubaneswar": "Odisha",
    "Indian Institute of Technology Bombay": "Maharashtra",
    "Indian Institute of Technology Mandi": "Himachal Pradesh",
    "Indian Institute of Technology Delhi": "Delhi",
    "Indian Institute of Technology Indore": "Madhya Pradesh",
    "Indian Institute of Technology Kharagpur": "West Bengal",
    "Indian Institute of Technology Hyderabad": "Telangana",
    "Indian Institute of Technology Jodhpur": "Rajasthan",
    "Indian Institute of Technology Kanpur": "Uttar Pradesh",
    "Indian Institute of Technology Madras": "Tamil Nadu",
    "Indian Institute of Technology Gandhinagar": "Gujarat",
    "Indian Institute of Technology Patna": "Bihar",
    "Indian Institute of Technology Roorkee": "Uttarakhand",
    "Indian Institute of Technology (ISM) Dhanbad": "Jharkhand",
    "Indian Institute of Technology Ropar": "Punjab",
    "Indian Institute of Technology (BHU) Varanasi": "Uttar Pradesh",
    "Indian Institute of Technology Guwahati": "Assam",
    "Indian Institute of Technology Bhilai": "Chhattisgarh",
    "Indian Institute of Technology Goa": "Goa",
    "Indian Institute of Technology Palakkad": "Kerala",
    "Indian Institute of Technology Tirupati": "Andhra Pradesh",
    "Indian Institute of Technology Jammu": "Jammu & Kashmir",
    "Indian Institute of Technology Dharwad": "Karnataka",
    # NITs
    "Dr. B R Ambedkar National Institute of Technology, Jalandhar": "Punjab",
    "Malaviya National Institute of Technology Jaipur": "Rajasthan",
    "Maulana Azad National Institute of Technology Bhopal": "Madhya Pradesh",
    "Motilal Nehru National Institute of Technology Allahabad": "Uttar Pradesh",
    "National Institute of Technology Agartala": "Tripura",
    "National Institute of Technology Calicut": "Kerala",
    "National Institute of Technology Delhi": "Delhi",
    "National Institute of Technology Durgapur": "West Bengal",
    "National Institute of Technology Goa": "Goa",
    "National Institute of Technology Hamirpur": "Himachal Pradesh",
    "National Institute of Technology Jamshedpur": "Jharkhand",
    "National Institute of Technology Karnataka, Surathkal": "Karnataka",
    "National Institute of Technology Kurukshetra": "Haryana",
    "National Institute of Technology Meghalaya": "Meghalaya",
    "National Institute of Technology Manipur": "Manipur",
    "National Institute of Technology Mizoram": "Mizoram",
    "National Institute of Technology Nagaland": "Nagaland",
    "National Institute of Technology Patna": "Bihar",
    "National Institute of Technology Puducherry": "Puducherry",
    "National Institute of Technology Raipur": "Chhattisgarh",
    "National Institute of Technology Rourkela": "Odisha",
    "National Institute of Technology Silchar": "Assam",
    "National Institute of Technology Srinagar": "Jammu & Kashmir",
    "National Institute of Technology Tiruchirappalli": "Tamil Nadu",
    "National Institute of Technology Uttarakhand": "Uttarakhand",
    "National Institute of Technology Warangal": "Telangana",
    "National Institute of Technology, Andhra Pradesh": "Andhra Pradesh",
    "National Institute of Technology Arunachal Pradesh": "Arunachal Pradesh",
    "National Institute of Technology Sikkim": "Sikkim",
    "Sardar Vallabhbhai National Institute of Technology, Surat": "Gujarat",
    "Visvesvaraya National Institute of Technology, Nagpur": "Maharashtra",
    # IIITs
    "Atal Bihari Vajpayee Indian Institute of Information Technology & Management Gwalior": "Madhya Pradesh",
    "Indian Institute of Information Technology, Allahabad": "Uttar Pradesh",
    "Indian Institute of Information Technology Guwahati": "Assam",
    "Indian Institute of Information Technology, Sri City, Chittoor": "Andhra Pradesh",
    "Indian Institute of Information Technology(IIIT) Kalyani, West Bengal": "West Bengal",
    "Indian Institute of Information Technology, Design & Manufacturing, Jabalpur": "Madhya Pradesh",
    "Indian Institute of Information Technology, Design and Manufacturing, Kancheepuram": "Tamil Nadu",
    "Indian Institute of Information Technology (IIIT), Kota, Rajasthan": "Rajasthan",
    "Indian Institute of Information Technology Lucknow": "Uttar Pradesh",
    "Indian Institute of Information Technology(IIIT), Nagpur": "Maharashtra",
    "Indian Institute of Information Technology (IIIT), Naya Raipur": "Chhattisgarh",
    "Indian Institute of Information Technology, Pune": "Maharashtra",
    "Indian Institute of Information Technology(IIIT) Ranchi": "Jharkhand",
    "Indian Institute of Information Technology(IIIT) Sonepat, Haryana": "Haryana",
    "Indian Institute of Information Technology(IIIT) Surat, Gujarat": "Gujarat",
    "Indian Institute of Information Technology, Tiruchirappalli": "Tamil Nadu",
    "Indian Institute of Information Technology Una, Himachal Pradesh": "Himachal Pradesh",
    "Indian Institute of Information Technology Vadodara, Gujarat": "Gujarat",
    "Indian Institute of Information Technology(IIIT), Vadodara International Campus Diu (IIITVICD)": "Daman & Diu",
    "Indian Institute of Information Technology, Design & Manufacturing, Kurnool": "Andhra Pradesh",
    "Indian Institute of Information Technology Dharwad": "Karnataka",
    "Indian Institute of Information Technology Bhagalpur": "Bihar",
    "Indian Institute of Information Technology Bhopal": "Madhya Pradesh",
    "Indian Institute of Information Technology, Kottayam": "Kerala",
    "INDIAN INSTITUTE OF INFORMATION TECHNOLOGY SENAPATI MANIPUR": "Manipur",
    "Indian institute of information technology, Raichur, Karnataka": "Karnataka",
    "Indian Institute of Information Technology Agartala": "Tripura",
    # GFTIs
    "Indian Institute of Engineering Science and Technology, Shibpur": "West Bengal",
    "Assam University, Silchar": "Assam",
    "Birla Institute of Technology, Mesra, Ranchi": "Jharkhand",
    "Birla Institute of Technology, Deoghar Off-Campus": "Jharkhand",
    "Birla Institute of Technology, Patna Off-Campus": "Bihar",
    "Gurukula Kangri Vishwavidyalaya, Haridwar": "Uttarakhand",
    "Indian Institute of Carpet Technology, Bhadohi": "Uttar Pradesh",
    "Institute of Infrastructure, Technology, Research and Management-Ahmedabad": "Gujarat",
    "School of Studies of Engineering and Technology, Guru Ghasidas Vishwavidyalaya, Bilaspur": "Chhattisgarh",
    "J.K. Institute of Applied Physics & Technology, Department of Electronics & Communication, University of Allahabad- Allahabad": "Uttar Pradesh",
    "National Institute of Electronics and Information Technology, Aurangabad (Maharashtra)": "Maharashtra",
    "National Institute of Advanced Manufacturing Technology, Ranchi": "Jharkhand",
    "Sant Longowal Institute of Engineering and Technology": "Punjab",
    "Mizoram University, Aizawl": "Mizoram",
    "School of Engineering, Tezpur University, Napaam, Tezpur": "Assam",
    "School of Planning & Architecture, Bhopal": "Madhya Pradesh",
    "School of Planning & Architecture, New Delhi": "Delhi",
    "School of Planning & Architecture: Vijayawada": "Andhra Pradesh",
    "Shri Mata Vaishno Devi University, Katra, Jammu & Kashmir": "Jammu & Kashmir",
    "International Institute of Information Technology, Naya Raipur": "Chhattisgarh",
    "University of Hyderabad": "Telangana",
    "Punjab Engineering College, Chandigarh": "Chandigarh",
    "Jawaharlal Nehru University, Delhi": "Delhi",
    "International Institute of Information Technology, Bhubaneswar": "Odisha",
    "Central institute of Technology Kokrajar, Assam": "Assam",
    "Puducherry Technological University, Puducherry": "Puducherry",
    "Ghani Khan Choudhary Institute of Engineering and Technology, Malda, West Bengal": "West Bengal",
    "Central University of Rajasthan, Rajasthan": "Rajasthan",
    "National Institute of Food Technology Entrepreneurship and Management, Kundli": "Haryana",
    "National Institute of Food Technology Entrepreneurship and Management, Thanjavur": "Tamil Nadu",
    "North Eastern Regional Institute of Science and Technology, Nirjuli-791109 (Itanagar),Arunachal Pradesh": "Arunachal Pradesh",
    "Indian Institute of Handloom Technology(IIHT), Varanasi": "Uttar Pradesh",
    "Chhattisgarh Swami Vivekanada Technical University, Bhilai (CSVTU Bhilai)": "Chhattisgarh",
    "Institute of Chemical Technology, Mumbai: Indian Oil Odisha Campus, Bhubaneswar": "Odisha",
    "North-Eastern Hill University, Shillong": "Meghalaya",
    "Central University of Jammu": "Jammu & Kashmir",
    "Institute of Engineering and Technology, Dr. H. S. Gour University. Sagar (A Central University)": "Madhya Pradesh",
    "Central University of Haryana": "Haryana",
    "Indian Institute of Handloom Technology, Salem": "Tamil Nadu",
    "Gati Shakti Vishwavidyalaya, Vadodara": "Gujarat",
    "CU Jharkhand": "Jharkhand",
}

# ─── Institute Short Name ───────────────────────────────────────────────────
def get_short_name(institute):
    """Generate a short display name for an institute."""
    # IITs
    if "Indian Institute of Technology" in institute:
        match = re.search(r'Indian Institute of Technology\s*(?:\((?:ISM|BHU)\))?\s*(.*)', institute)
        if match:
            suffix = match.group(1).strip().rstrip('.')
            if "(ISM)" in institute:
                return f"IIT (ISM) Dhanbad"
            if "(BHU)" in institute:
                return f"IIT (BHU) Varanasi"
            return f"IIT {suffix}"
        return institute

    # NITs
    if "National Institute of Technology" in institute:
        name = institute.replace("National Institute of Technology", "").strip().strip(",").strip()
        if "Dr. B R Ambedkar" in institute:
            return "NIT Jalandhar"
        if "Malaviya" in institute:
            return "MNIT Jaipur"
        if "Maulana Azad" in institute:
            return "MANIT Bhopal"
        if "Motilal Nehru" in institute:
            return "MNNIT Allahabad"
        if "Sardar Vallabhbhai" in institute:
            return "SVNIT Surat"
        if "Visvesvaraya" in institute:
            return "VNIT Nagpur"
        if "Karnataka" in institute:
            return "NIT Surathkal"
        return f"NIT {name}"

    # IIITs
    if "Indian Institute of Information Technology" in institute or "IIIT" in institute.upper():
        # Extract city name
        for city in ["Allahabad", "Gwalior", "Jabalpur", "Kancheepuram", "Kurnool",
                      "Sri City", "Guwahati", "Kalyani", "Kota", "Kottayam", "Lucknow",
                      "Nagpur", "Pune", "Raichur", "Ranchi", "Sonepat", "Surat",
                      "Tiruchirappalli", "Una", "Vadodara", "Dharwad", "Bhagalpur",
                      "Bhopal", "Agartala", "Manipur", "Naya Raipur"]:
            if city.lower() in institute.lower():
                if "Design & Manufacturing" in institute or "Design and Manufacturing" in institute:
                    return f"IIITDM {city}"
                if "Management" in institute and "Gwalior" in institute:
                    return f"ABV-IIITM Gwalior"
                return f"IIIT {city}"
        if "IIITVICD" in institute or "Diu" in institute:
            return "IIIT Vadodara (IIITVICD)"
        return institute[:40]

    # GFTIs — specific short names
    short_map = {
        "Indian Institute of Engineering Science and Technology, Shibpur": "IIEST Shibpur",
        "Birla Institute of Technology, Mesra, Ranchi": "BIT Mesra",
        "Birla Institute of Technology, Deoghar Off-Campus": "BIT Deoghar",
        "Birla Institute of Technology, Patna Off-Campus": "BIT Patna",
        "Punjab Engineering College, Chandigarh": "PEC Chandigarh",
        "Sant Longowal Institute of Engineering and Technology": "SLIET Longowal",
        "Shri Mata Vaishno Devi University, Katra, Jammu & Kashmir": "SMVDU Katra",
        "International Institute of Information Technology, Naya Raipur": "IIIT Naya Raipur",
        "International Institute of Information Technology, Bhubaneswar": "IIIT Bhubaneswar",
        "Puducherry Technological University, Puducherry": "PTU Puducherry",
        "Jawaharlal Nehru University, Delhi": "JNU Delhi",
    }
    if institute in short_map:
        return short_map[institute]

    # Fallback: truncate
    return institute[:50]


def get_institute_type(institute):
    """Detect institute type: IIT, NIT, IIIT, or GFTI."""
    inst_lower = institute.lower()
    if "indian institute of technology" in inst_lower:
        return "IIT"
    if "national institute of technology" in inst_lower or \
       "malaviya national" in inst_lower or \
       "maulana azad national" in inst_lower or \
       "motilal nehru national" in inst_lower or \
       "dr. b r ambedkar national" in inst_lower or \
       "sardar vallabhbhai national" in inst_lower or \
       "visvesvaraya national" in inst_lower:
        return "NIT"
    if "indian institute of information technology" in inst_lower or \
       "iiit" in inst_lower:
        return "IIIT"
    return "GFTI"


def extract_branch_name(program_name):
    """Extract core branch name from full program string.
    E.g. 'Computer Science and Engineering (4 Years, Bachelor of Technology)' → 'Computer Science and Engineering'
    """
    # Remove degree info in parentheses at the end
    # Pattern: "Branch Name (X Years, Degree Type)" or "Branch Name (X Years, ...)"
    match = re.match(r'^(.*?)\s*\(\d+\s*Years?,.*\)\s*$', program_name)
    if match:
        return match.group(1).strip()

    # Some have "B.Tech in ..." format
    match = re.match(r'^B\.?Tech\.?\s+in\s+(.*?)\s*\(\d+\s*Years?,.*\)\s*$', program_name, re.IGNORECASE)
    if match:
        return "B.Tech in " + match.group(1).strip()

    return program_name.strip()


def normalize_branch(branch_name):
    """Normalize branch name to a standard short name."""
    # First try exact match
    if branch_name in BRANCH_NORMALIZE:
        return BRANCH_NORMALIZE[branch_name]

    # Try partial matching
    branch_lower = branch_name.lower()
    for key, value in BRANCH_NORMALIZE.items():
        if key.lower() == branch_lower:
            return value

    # Fallback: return cleaned name
    return branch_name


def get_degree_type(program_name):
    """Extract degree type from program name."""
    prog_lower = program_name.lower()
    if "dual degree" in prog_lower or "bachelor and master" in prog_lower:
        return "Dual Degree (B.Tech + M.Tech)"
    if "integrated" in prog_lower:
        return "Integrated"
    if "bachelor of architecture" in prog_lower or "b.arch" in prog_lower:
        return "B.Arch"
    if "bachelor of science" in prog_lower or "b.s" in prog_lower:
        return "B.S."
    if "bachelor of planning" in prog_lower:
        return "B.Planning"
    if "bachelor of design" in prog_lower:
        return "B.Des"
    return "B.Tech"


def get_duration(program_name):
    """Extract duration from program name."""
    match = re.search(r'(\d+)\s*Years?', program_name)
    if match:
        return int(match.group(1))
    return 4


def process_all_files(data_dir):
    """Process all Excel files and return combined DataFrame."""

    # Files to process — we use last round per year for closing cutoffs
    files = [
        "2021Round1.xlsx", "2021Round6.xlsx",
        "2022Round1.xlsx", "2022Round6.xlsx",
        "2023Round1.xlsx", "2023Round6.xlsx",
        "2024Round1.xlsx", "2024Round5.xlsx",
    ]

    all_data = []

    for filename in files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"  ⚠ File not found: {filename}, skipping...")
            continue

        print(f"  📂 Processing {filename}...")
        df = pd.read_excel(filepath)

        # Standardize column names
        df.columns = df.columns.str.strip()

        all_data.append(df)
        print(f"     → {len(df)} rows loaded")

    if not all_data:
        print("❌ No data files found!")
        return None

    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n📊 Combined: {len(combined)} total rows")

    return combined


def clean_and_enrich(df):
    """Clean data and add enriched columns."""

    print("\n🔧 Cleaning and enriching data...")

    # Remove rows with missing critical fields
    df = df.dropna(subset=['Institute', 'Academic Program Name', 'Closing Rank'])

    # Clean rank columns — handle non-numeric values
    for col in ['Opening Rank', 'Closing Rank']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Closing Rank'])
    df['Opening Rank'] = df['Opening Rank'].fillna(df['Closing Rank'])
    df['Opening Rank'] = df['Opening Rank'].astype(int)
    df['Closing Rank'] = df['Closing Rank'].astype(int)

    # Extract and normalize branch names
    df['branch_full'] = df['Academic Program Name'].apply(extract_branch_name)
    df['branch_short'] = df['branch_full'].apply(normalize_branch)
    df['degree_type'] = df['Academic Program Name'].apply(get_degree_type)
    df['duration'] = df['Academic Program Name'].apply(get_duration)

    # Institute metadata
    df['institute_type'] = df['Institute'].apply(get_institute_type)
    df['institute_short'] = df['Institute'].apply(get_short_name)
    df['state'] = df['Institute'].map(INSTITUTE_STATE).fillna('Unknown')

    # Clean seat type
    df['Seat Type'] = df['Seat Type'].str.strip()
    df['Gender'] = df['Gender'].str.strip()
    df['Quota'] = df['Quota'].str.strip()

    print(f"  ✅ After cleaning: {len(df)} rows")
    print(f"  📍 Institute types: {df['institute_type'].value_counts().to_dict()}")
    print(f"  📍 Unique branches (normalized): {df['branch_short'].nunique()}")
    print(f"  📍 Years: {sorted(df['Year'].unique())}")
    print(f"  📍 Rounds: {sorted(df['Round'].unique())}")

    return df


def export_data(df, output_dir):
    """Export processed data to JSON."""

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cutoffs_processed.json")

    # Convert to records
    records = []
    for _, row in df.iterrows():
        records.append({
            "institute": row["Institute"],
            "institute_short": row["institute_short"],
            "institute_type": row["institute_type"],
            "state": row["state"],
            "program": row["Academic Program Name"],
            "branch_full": row["branch_full"],
            "branch_short": row["branch_short"],
            "degree_type": row["degree_type"],
            "duration": int(row["duration"]),
            "quota": row["Quota"],
            "seat_type": row["Seat Type"],
            "gender": row["Gender"],
            "opening_rank": int(row["Opening Rank"]),
            "closing_rank": int(row["Closing Rank"]),
            "year": int(row["Year"]),
            "round": int(row["Round"]),
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Exported {len(records)} records to {output_path}")

    # Also export metadata
    meta = {
        "total_records": len(records),
        "institutes": sorted(df["Institute"].unique().tolist()),
        "institute_types": sorted(df["institute_type"].unique().tolist()),
        "branches": sorted(df["branch_short"].unique().tolist()),
        "seat_types": sorted(df["Seat Type"].unique().tolist()),
        "genders": sorted(df["Gender"].unique().tolist()),
        "quotas": sorted(df["Quota"].unique().tolist()),
        "years": sorted(df["Year"].unique().tolist()),
        "states": sorted(df["state"].unique().tolist()),
    }
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"📋 Metadata saved to {meta_path}")

    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("  JoSAA Data Processor")
    print("=" * 60)

    # Paths — Excel files are in the project root (two levels up from this script)
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    output_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"\n📁 Reading Excel files from: {data_dir}")

    # Process
    df = process_all_files(data_dir)
    if df is not None:
        df = clean_and_enrich(df)
        export_data(df, output_dir)
        print("\n✅ Data processing complete!")
    else:
        print("\n❌ Data processing failed!")
