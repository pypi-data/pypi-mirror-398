from typing import List, Union, Optional
from enum import Enum
from pydantic import BaseModel, Field


class CleanlinessLevel(str, Enum):
    """Enumeration for cleanliness condition."""
    CLEAN = "Clean"
    SLIGHTLY_DUSTY = "Slightly Dusty"
    NEEDS_CLEANING = "Needs Cleaning"


class InkWallAnalysis(BaseModel):
    """Schema for a detailed retail ink-wall analysis."""
    epson_product_count: int = Field(
        ...,
        description="The total count of all visible Epson branded products (boxed or unboxed)."
    )
    competitor_product_count: int = Field(
        ...,
        description="The total count of all visible competitor products (HP, Canon, Brother, Xerox, Lexmark, Ricoh, Kyocera)."
    )
    competitors_found: List[str] = Field(
        ...,
        description="A list of competitor brand names found on the shelves."
    )
    shelf_occupancy_percentage: float = Field(
        ...,
        description="An estimated percentage of how full the shelves are overall (0-100)."
    )
    shelf_stocking: str = Field(
        ...,
        description="A brief description of the stocking condition, e.g., 'well-stocked', 'moderately stocked', 'needs restocking', 'sparsely stocked', 'out of stock'."
    )
    overall_condition: str = Field(
        ...,
        description="A brief description of the overall condition of the ink wall, evaluate product alignment, cleanliness, and any visible damage"
    )
    has_gaps: bool = Field(
        ...,
        description="True if there are noticeable empty spaces or gaps on the shelves where products should be."
    )
    gaps_description: Optional[str] = Field(
        None,
        description="A brief description of where the most significant gaps are located."
    )
    restocking_needed: bool = Field(
        ...,
        description="True if the gaps or low stock levels suggest that restocking is required."
    )
    is_shelf_empty: bool = Field(
        ...,
        description="True if any single shelf is completely empty, otherwise False."
    )
    misplaced_products_found: bool = Field(
        ...,
        description="True if any product appears to be in the wrong location (e.g., an HP cartridge in an Epson section)."
    )
    cleanliness_condition: CleanlinessLevel = Field(
        ...,
        description="The overall cleanliness of the shelves and products."
    )
    trash_present: bool = Field(
        ...,
        description="True if any visible trash, debris, or stray packaging is present on the shelves or floor."
    )


class ShelvesWithProductsAnalysis(BaseModel):
    """Schema for analyzing shelves with products in a retail setting."""
    epson_product_count: int = Field(
        ...,
        description="The total count of all visible Epson branded products (boxed or unboxed)."
    )
    competitor_product_count: int = Field(
        ...,
        description="The total count of all visible competitor products (HP, Canon, Brother, Xerox, Lexmark, Ricoh, Kyocera)."
    )
    competitors_found: List[str] = Field(
        ...,
        description="A list of competitor brand names found on the shelves."
    )
    shelf_occupancy_percentage: float = Field(
        ...,
        description="An estimated percentage of how full the shelves are overall (0-100)."
    )
    shelf_stocking: str = Field(
        ...,
        description="A brief description of the stocking condition, e.g., 'well-stocked', 'moderately stocked', 'needs restocking', 'sparsely stocked', 'out of stock'."
    )
    overall_condition: str = Field(
        ...,
        description="A brief description of the overall condition of the shelves, evaluate product alignment, cleanliness, and any visible damage."
    )
    misplaced_products_found: bool = Field(
        ...,
        description="True if any product appears to be in the wrong location (e.g., an HP cartridge in an Epson section)."
    )


class BoxesOnFloorAnalysis(BaseModel):
    """Schema for analyzing boxes on the floor in a retail setting."""
    epson_product_count: int = Field(
        ...,
        description="The total count of all visible Epson branded products (boxed or unboxed) found in the boxes."
    )
    competitor_product_count: int = Field(
        ...,
        description="The total count of all visible competitor products (HP, Canon, Brother, Xerox, Lexmark, Ricoh, Kyocera) found in the boxes."
    )
    competitors_found: List[str] = Field(
        ...,
        description="A list of competitor brand names found in the boxes."
    )
    box_condition: str = Field(
        ...,
        description="A brief description of the condition of the boxes, e.g., 'intact', 'damaged', 'partially open'."
    )
    cleanliness_condition: CleanlinessLevel = Field(
        ...,
        description="The overall cleanliness of the boxes and their contents."
    )
    trash_present: bool = Field(
        ...,
        description="True if any visible trash, debris, or stray packaging is present around the boxes."
    )
    pricing_labels_present: bool = Field(
        ...,
        description="True if any pricing labels or tags are visible on the boxes."
    )


class MerchandisingEndcapAnalysis(BaseModel):
    """Schema for analyzing merchandising endcaps in a retail setting."""
    brand_presence: str = Field(
        ...,
        description="The brand presence on the endcap, e.g., 'Epson', 'Competitor', 'Mixed'."
    )
    merchandising_quality: str = Field(
        ...,
        description="A brief description of the merchandising quality, e.g., 'well-presented', 'moderately presented', 'poorly presented'."
    )
    product_count: int = Field(
        ...,
        description="The total count of products displayed on the endcap."
    )
    product_types: List[str] = Field(
        ...,
        description="A list of product types or categories displayed on the endcap."
    )
    promotional_materials_present: bool = Field(
        ...,
        description="True if any promotional materials (banners, signs, etc.) are present on the endcap."
    )
    cleanliness_condition: CleanlinessLevel = Field(
        ...,
        description="The overall cleanliness of the endcap and its products."
    )
    trash_present: bool = Field(
        ...,
        description="True if any visible trash, debris, or stray packaging is present on the endcap."
    )
    overall_condition: str = Field(
        ...,
        description="A brief description of the overall condition of the endcap, evaluate product alignment, cleanliness, and any visible damage."
    )

__all__ = [
    'CleanlinessLevel',
    'InkWallAnalysis',
    'ShelvesWithProductsAnalysis',
    'BoxesOnFloorAnalysis',
    'MerchandisingEndcapAnalysis'
]
