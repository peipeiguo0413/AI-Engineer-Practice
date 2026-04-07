from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Condition(str, Enum):
    excellent  = "excellent"
    good       = "good"
    fair       = "fair"
    poor       = "poor"
    unknown    = "unknown"

class FlooringType(str, Enum):
    hardwood   = "hardwood"
    carpet     = "carpet"
    tile       = "tile"
    lvp        = "lvp"
    mixed      = "mixed"
    other      = "other"

class InteriorConditionForm(BaseModel):
    address:               str   = Field(..., description="Full property address")
    asking_price:          float = Field(..., description="Asking price in USD")
    sqft:                  int   = Field(..., description="Square footage")
    bedrooms:              int   = Field(..., description="Number of bedrooms")
    bathrooms:             float = Field(..., description="Number of bathrooms")
    year_built:            int   = Field(..., description="Year the property was built")
    report_type:           str   = Field("buyer")
    kitchen_renovated:     bool           = Field(False)
    kitchen_reno_year:     Optional[int]  = Field(None)
    kitchen_condition:     Condition      = Field(Condition.good)
    master_bath_renovated: bool           = Field(False)
    master_bath_reno_year: Optional[int]  = Field(None)
    other_baths_condition: Condition      = Field(Condition.good)
    flooring_type:         FlooringType   = Field(FlooringType.mixed)
    flooring_age_years:    Optional[int]  = Field(None)
    flooring_condition:    Condition      = Field(Condition.good)
    roof_age_years:        Optional[int]  = Field(None)
    roof_condition:        Condition      = Field(Condition.good)
    foundation_issues:     bool           = Field(False)
    furnace_age_years:     Optional[int]  = Field(None)
    ac_age_years:          Optional[int]  = Field(None)
    water_heater_age:      Optional[int]  = Field(None)
    recent_upgrades:       Optional[str]  = Field(None)
    known_issues:          Optional[str]  = Field(None)
    expected_monthly_rent: Optional[float] = Field(None)
    monthly_expenses:      Optional[float] = Field(None)
