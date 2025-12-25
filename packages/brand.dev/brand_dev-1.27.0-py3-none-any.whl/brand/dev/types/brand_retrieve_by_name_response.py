# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = [
    "BrandRetrieveByNameResponse",
    "Brand",
    "BrandAddress",
    "BrandBackdrop",
    "BrandBackdropColor",
    "BrandBackdropResolution",
    "BrandColor",
    "BrandIndustries",
    "BrandIndustriesEic",
    "BrandLinks",
    "BrandLogo",
    "BrandLogoColor",
    "BrandLogoResolution",
    "BrandSocial",
    "BrandStock",
]


class BrandAddress(BaseModel):
    """Physical address of the brand"""

    city: Optional[str] = None
    """City name"""

    country: Optional[str] = None
    """Country name"""

    country_code: Optional[str] = None
    """Country code"""

    postal_code: Optional[str] = None
    """Postal or ZIP code"""

    state_code: Optional[str] = None
    """State or province code"""

    state_province: Optional[str] = None
    """State or province name"""

    street: Optional[str] = None
    """Street address"""


class BrandBackdropColor(BaseModel):
    hex: Optional[str] = None
    """Color in hexadecimal format"""

    name: Optional[str] = None
    """Name of the color"""


class BrandBackdropResolution(BaseModel):
    """Resolution of the backdrop image"""

    aspect_ratio: Optional[float] = None
    """Aspect ratio of the image (width/height)"""

    height: Optional[int] = None
    """Height of the image in pixels"""

    width: Optional[int] = None
    """Width of the image in pixels"""


class BrandBackdrop(BaseModel):
    colors: Optional[List[BrandBackdropColor]] = None
    """Array of colors in the backdrop image"""

    resolution: Optional[BrandBackdropResolution] = None
    """Resolution of the backdrop image"""

    url: Optional[str] = None
    """URL of the backdrop image"""


class BrandColor(BaseModel):
    hex: Optional[str] = None
    """Color in hexadecimal format"""

    name: Optional[str] = None
    """Name of the color"""


class BrandIndustriesEic(BaseModel):
    industry: Literal[
        "Aerospace & Defense",
        "Technology",
        "Finance",
        "Healthcare",
        "Retail & E-commerce",
        "Entertainment",
        "Education",
        "Government & Nonprofit",
        "Industrial & Energy",
        "Automotive & Transportation",
        "Lifestyle & Leisure",
        "Luxury & Fashion",
        "News & Media",
        "Sports",
        "Real Estate & PropTech",
        "Legal & Compliance",
        "Telecommunications",
        "Agriculture & Food",
        "Professional Services & Agencies",
        "Chemicals & Materials",
        "Logistics & Supply Chain",
        "Hospitality & Tourism",
        "Construction & Built Environment",
        "Consumer Packaged Goods (CPG)",
    ]
    """Industry classification enum"""

    subindustry: Literal[
        "Defense Systems & Military Hardware",
        "Aerospace Manufacturing",
        "Avionics & Navigation Technology",
        "Subsea & Naval Defense Systems",
        "Space & Satellite Technology",
        "Defense IT & Systems Integration",
        "Software (B2B)",
        "Software (B2C)",
        "Cloud Infrastructure & DevOps",
        "Cybersecurity",
        "Artificial Intelligence & Machine Learning",
        "Data Infrastructure & Analytics",
        "Hardware & Semiconductors",
        "Fintech Infrastructure",
        "eCommerce & Marketplace Platforms",
        "Developer Tools & APIs",
        "Web3 & Blockchain",
        "XR & Spatial Computing",
        "Banking & Lending",
        "Investment Management & WealthTech",
        "Insurance & InsurTech",
        "Payments & Money Movement",
        "Accounting, Tax & Financial Planning Tools",
        "Capital Markets & Trading Platforms",
        "Financial Infrastructure & APIs",
        "Credit Scoring & Risk Management",
        "Cryptocurrency & Digital Assets",
        "BNPL & Alternative Financing",
        "Healthcare Providers & Services",
        "Pharmaceuticals & Drug Development",
        "Medical Devices & Diagnostics",
        "Biotechnology & Genomics",
        "Digital Health & Telemedicine",
        "Health Insurance & Benefits Tech",
        "Clinical Trials & Research Platforms",
        "Mental Health & Wellness",
        "Healthcare IT & EHR Systems",
        "Consumer Health & Wellness Products",
        "Online Marketplaces",
        "Direct-to-Consumer (DTC) Brands",
        "Retail Tech & Point-of-Sale Systems",
        "Omnichannel & In-Store Retail",
        "E-commerce Enablement & Infrastructure",
        "Subscription & Membership Commerce",
        "Social Commerce & Influencer Platforms",
        "Fashion & Apparel Retail",
        "Food, Beverage & Grocery E-commerce",
        "Streaming Platforms (Video, Music, Audio)",
        "Gaming & Interactive Entertainment",
        "Creator Economy & Influencer Platforms",
        "Advertising, Adtech & Media Buying",
        "Film, TV & Production Studios",
        "Events, Venues & Live Entertainment",
        "Virtual Worlds & Metaverse Experiences",
        "K-12 Education Platforms & Tools",
        "Higher Education & University Tech",
        "Online Learning & MOOCs",
        "Test Prep & Certification",
        "Corporate Training & Upskilling",
        "Tutoring & Supplemental Learning",
        "Education Management Systems (LMS/SIS)",
        "Language Learning",
        "Creator-Led & Cohort-Based Courses",
        "Special Education & Accessibility Tools",
        "Government Technology & Digital Services",
        "Civic Engagement & Policy Platforms",
        "International Development & Humanitarian Aid",
        "Philanthropy & Grantmaking",
        "Nonprofit Operations & Fundraising Tools",
        "Public Health & Social Services",
        "Education & Youth Development Programs",
        "Environmental & Climate Action Organizations",
        "Legal Aid & Social Justice Advocacy",
        "Municipal & Infrastructure Services",
        "Manufacturing & Industrial Automation",
        "Energy Production (Oil, Gas, Nuclear)",
        "Renewable Energy & Cleantech",
        "Utilities & Grid Infrastructure",
        "Industrial IoT & Monitoring Systems",
        "Construction & Heavy Equipment",
        "Mining & Natural Resources",
        "Environmental Engineering & Sustainability",
        "Energy Storage & Battery Technology",
        "Automotive OEMs & Vehicle Manufacturing",
        "Electric Vehicles (EVs) & Charging Infrastructure",
        "Mobility-as-a-Service (MaaS)",
        "Fleet Management",
        "Public Transit & Urban Mobility",
        "Autonomous Vehicles & ADAS",
        "Aftermarket Parts & Services",
        "Telematics & Vehicle Connectivity",
        "Aviation & Aerospace Transport",
        "Maritime Shipping",
        "Fitness & Wellness",
        "Beauty & Personal Care",
        "Home & Living",
        "Dating & Relationships",
        "Hobbies, Crafts & DIY",
        "Outdoor & Recreational Gear",
        "Events, Experiences & Ticketing Platforms",
        "Designer & Luxury Apparel",
        "Accessories, Jewelry & Watches",
        "Footwear & Leather Goods",
        "Beauty, Fragrance & Skincare",
        "Fashion Marketplaces & Retail Platforms",
        "Sustainable & Ethical Fashion",
        "Resale, Vintage & Circular Fashion",
        "Fashion Tech & Virtual Try-Ons",
        "Streetwear & Emerging Luxury",
        "Couture & Made-to-Measure",
        "News Publishing & Journalism",
        "Digital Media & Content Platforms",
        "Broadcasting (TV & Radio)",
        "Podcasting & Audio Media",
        "News Aggregators & Curation Tools",
        "Independent & Creator-Led Media",
        "Newsletters & Substack-Style Platforms",
        "Political & Investigative Media",
        "Trade & Niche Publications",
        "Media Monitoring & Analytics",
        "Professional Teams & Leagues",
        "Sports Media & Broadcasting",
        "Sports Betting & Fantasy Sports",
        "Fitness & Athletic Training Platforms",
        "Sportswear & Equipment",
        "Esports & Competitive Gaming",
        "Sports Venues & Event Management",
        "Athlete Management & Talent Agencies",
        "Sports Tech & Performance Analytics",
        "Youth, Amateur & Collegiate Sports",
        "Real Estate Marketplaces",
        "Property Management Software",
        "Rental Platforms",
        "Mortgage & Lending Tech",
        "Real Estate Investment Platforms",
        "Law Firms & Legal Services",
        "Legal Tech & Automation",
        "Regulatory Compliance",
        "E-Discovery & Litigation Tools",
        "Contract Management",
        "Governance, Risk & Compliance (GRC)",
        "IP & Trademark Management",
        "Legal Research & Intelligence",
        "Compliance Training & Certification",
        "Whistleblower & Ethics Reporting",
        "Mobile & Wireless Networks (3G/4G/5G)",
        "Broadband & Fiber Internet",
        "Satellite & Space-Based Communications",
        "Network Equipment & Infrastructure",
        "Telecom Billing & OSS/BSS Systems",
        "VoIP & Unified Communications",
        "Internet Service Providers (ISPs)",
        "Edge Computing & Network Virtualization",
        "IoT Connectivity Platforms",
        "Precision Agriculture & AgTech",
        "Crop & Livestock Production",
        "Food & Beverage Manufacturing & Processing",
        "Food Distribution",
        "Restaurants & Food Service",
        "Agricultural Inputs & Equipment",
        "Sustainable & Regenerative Agriculture",
        "Seafood & Aquaculture",
        "Management Consulting",
        "Marketing & Advertising Agencies",
        "Design, Branding & Creative Studios",
        "IT Services & Managed Services",
        "Staffing, Recruiting & Talent",
        "Accounting & Tax Firms",
        "Public Relations & Communications",
        "Business Process Outsourcing (BPO)",
        "Professional Training & Coaching",
        "Specialty Chemicals",
        "Commodity & Petrochemicals",
        "Polymers, Plastics & Rubber",
        "Coatings, Adhesives & Sealants",
        "Industrial Gases",
        "Advanced Materials & Composites",
        "Battery Materials & Energy Storage",
        "Electronic Materials & Semiconductor Chemicals",
        "Agrochemicals & Fertilizers",
        "Freight & Transportation Tech",
        "Last-Mile Delivery",
        "Warehouse Automation",
        "Supply Chain Visibility Platforms",
        "Logistics Marketplaces",
        "Shipping & Freight Forwarding",
        "Cold Chain Logistics",
        "Reverse Logistics & Returns",
        "Cross-Border Trade Tech",
        "Transportation Management Systems (TMS)",
        "Hotels & Accommodation",
        "Vacation Rentals & Short-Term Stays",
        "Restaurant Tech & Management",
        "Travel Booking Platforms",
        "Tourism Experiences & Activities",
        "Cruise Lines & Marine Tourism",
        "Hospitality Management Systems",
        "Event & Venue Management",
        "Corporate Travel Management",
        "Travel Insurance & Protection",
        "Construction Management Software",
        "BIM/CAD & Design Tools",
        "Construction Marketplaces",
        "Equipment Rental & Management",
        "Building Materials & Procurement",
        "Construction Workforce Management",
        "Project Estimation & Bidding",
        "Modular & Prefab Construction",
        "Construction Safety & Compliance",
        "Smart Building Technology",
        "Food & Beverage CPG",
        "Home & Personal Care CPG",
        "CPG Analytics & Insights",
        "Direct-to-Consumer CPG Brands",
        "CPG Supply Chain & Distribution",
        "Private Label Manufacturing",
        "CPG Retail Intelligence",
        "Sustainable CPG & Packaging",
        "Beauty & Cosmetics CPG",
        "Health & Wellness CPG",
    ]
    """Subindustry classification enum"""


class BrandIndustries(BaseModel):
    """Industry classification information for the brand"""

    eic: Optional[List[BrandIndustriesEic]] = None
    """Easy Industry Classification - array of industry and subindustry pairs"""


class BrandLinks(BaseModel):
    """Important website links for the brand"""

    blog: Optional[str] = None
    """URL to the brand's blog or news page"""

    careers: Optional[str] = None
    """URL to the brand's careers or job opportunities page"""

    contact: Optional[str] = None
    """URL to the brand's contact or contact us page"""

    pricing: Optional[str] = None
    """URL to the brand's pricing or plans page"""

    privacy: Optional[str] = None
    """URL to the brand's privacy policy page"""

    terms: Optional[str] = None
    """URL to the brand's terms of service or terms and conditions page"""


class BrandLogoColor(BaseModel):
    hex: Optional[str] = None
    """Color in hexadecimal format"""

    name: Optional[str] = None
    """Name of the color"""


class BrandLogoResolution(BaseModel):
    """Resolution of the logo image"""

    aspect_ratio: Optional[float] = None
    """Aspect ratio of the image (width/height)"""

    height: Optional[int] = None
    """Height of the image in pixels"""

    width: Optional[int] = None
    """Width of the image in pixels"""


class BrandLogo(BaseModel):
    colors: Optional[List[BrandLogoColor]] = None
    """Array of colors in the logo"""

    mode: Optional[Literal["light", "dark", "has_opaque_background"]] = None
    """
    Indicates when this logo is best used: 'light' = best for light mode, 'dark' =
    best for dark mode, 'has_opaque_background' = can be used for either as image
    has its own background
    """

    resolution: Optional[BrandLogoResolution] = None
    """Resolution of the logo image"""

    type: Optional[Literal["icon", "logo"]] = None
    """Type of the logo based on resolution (e.g., 'icon', 'logo')"""

    url: Optional[str] = None
    """CDN hosted url of the logo (ready for display)"""


class BrandSocial(BaseModel):
    type: Optional[str] = None
    """Type of social media, e.g., 'facebook', 'twitter'"""

    url: Optional[str] = None
    """URL of the social media page"""


class BrandStock(BaseModel):
    """
    Stock market information for this brand (will be null if not a publicly traded company)
    """

    exchange: Optional[str] = None
    """Stock exchange name"""

    ticker: Optional[str] = None
    """Stock ticker symbol"""


class Brand(BaseModel):
    """Detailed brand information"""

    address: Optional[BrandAddress] = None
    """Physical address of the brand"""

    backdrops: Optional[List[BrandBackdrop]] = None
    """An array of backdrop images for the brand"""

    colors: Optional[List[BrandColor]] = None
    """An array of brand colors"""

    description: Optional[str] = None
    """A brief description of the brand"""

    domain: Optional[str] = None
    """The domain name of the brand"""

    email: Optional[str] = None
    """Company email address"""

    industries: Optional[BrandIndustries] = None
    """Industry classification information for the brand"""

    is_nsfw: Optional[bool] = None
    """Indicates whether the brand content is not safe for work (NSFW)"""

    links: Optional[BrandLinks] = None
    """Important website links for the brand"""

    logos: Optional[List[BrandLogo]] = None
    """An array of logos associated with the brand"""

    phone: Optional[str] = None
    """Company phone number"""

    slogan: Optional[str] = None
    """The brand's slogan"""

    socials: Optional[List[BrandSocial]] = None
    """An array of social media links for the brand"""

    stock: Optional[BrandStock] = None
    """
    Stock market information for this brand (will be null if not a publicly traded
    company)
    """

    title: Optional[str] = None
    """The title or name of the brand"""


class BrandRetrieveByNameResponse(BaseModel):
    brand: Optional[Brand] = None
    """Detailed brand information"""

    code: Optional[int] = None
    """HTTP status code"""

    status: Optional[str] = None
    """Status of the response, e.g., 'ok'"""
