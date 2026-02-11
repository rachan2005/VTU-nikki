"""VTU Skills - Curated list relevant to actual work"""

VTU_SKILLS = [
    "AWS",
    "Azure",
    "C++",
    "Canva",
    "Cloud access control",
    "CSS",
    "Data encryption",
    "Data modeling",
    "Data visualization",
    "Database design",
    "DevOps",
    "Digital Design",
    "Docker",
    "Figma",
    "Git",
    "Godot",
    "Google Cloud",
    "HTML",
    "IaaS",
    "Indexing",
    "JavaScript",
    "Machine learning",
    "MySQL",
    "Network architecture",
    "Node.js",
    "NoSQL",
    "Physical Design",
    "PostgreSQL",
    "Python",
    "PyTorch",
    "React",
    "React.js",
    "SaaS",
    "scikit-learn",
    "SEO",
    "SQL",
    "Statistical analysis",
    "Swift",
    "Tableau",
    "TCP/IP",
    "TensorFlow",
    "TypeScript",
    "UI/UX",
]


def get_skills_list():
    """Get the complete list of VTU skills"""
    return VTU_SKILLS


def format_skills_for_prompt():
    """Format skills list for LLM prompt"""
    return "\n".join([f"- {skill}" for skill in VTU_SKILLS])
