from dataclasses import dataclass
from typing import Any


@dataclass
class OrderData:
    """Order resource data."""

    id: int
    # Core fields
    id_customer: int | None = None
    id_cart: int | None = None
    id_currency: int | None = None
    id_lang: int | None = None
    id_address_delivery: int | None = None
    id_address_invoice: int | None = None
    id_carrier: int | None = None
    id_shop: int | None = None
    id_shop_group: int | None = None
    current_state: int | None = None
    reference: str | None = None
    secure_key: str | None = None
    payment: str | None = None
    module: str | None = None
    # Totals
    total_paid: str | None = None
    total_paid_tax_incl: str | None = None
    total_paid_tax_excl: str | None = None
    total_paid_real: str | None = None
    total_products: str | None = None
    total_products_wt: str | None = None
    total_shipping: str | None = None
    total_shipping_tax_incl: str | None = None
    total_shipping_tax_excl: str | None = None
    total_discounts: str | None = None
    total_discounts_tax_incl: str | None = None
    total_discounts_tax_excl: str | None = None
    total_wrapping: str | None = None
    total_wrapping_tax_incl: str | None = None
    total_wrapping_tax_excl: str | None = None
    # Other fields
    carrier_tax_rate: str | None = None
    conversion_rate: str | None = None
    round_mode: int | None = None
    round_type: int | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    delivery_number: str | None = None
    delivery_date: str | None = None
    shipping_number: str | None = None
    note: str | None = None
    valid: int | None = None
    date_add: str | None = None
    date_upd: str | None = None
    associations: dict[str, Any] | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class CustomerData:
    """Customer resource data."""

    id: int
    # Core fields
    id_default_group: int | None = None
    id_lang: int | None = None
    id_shop: int | None = None
    id_shop_group: int | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    active: int | None = None
    date_add: str | None = None
    date_upd: str | None = None
    # Optional fields
    id_gender: int | None = None
    birthday: str | None = None
    newsletter: int | None = None
    optin: int | None = None
    website: str | None = None
    company: str | None = None
    siret: str | None = None
    ape: str | None = None
    outstanding_allow_amount: str | None = None
    max_payment_days: int | None = None
    note: str | None = None
    secure_key: str | None = None
    # Extra fields from API
    passwd: str | None = None
    last_passwd_gen: str | None = None
    newsletter_date_add: str | None = None
    reset_password_validity: str | None = None
    associations: dict[str, Any] | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class ProductData:
    """Product resource data."""

    id: int
    # Core fields
    id_manufacturer: int | None = None
    id_supplier: int | None = None
    id_category_default: int | None = None
    id_shop_default: int | None = None
    id_tax_rules_group: int | None = None
    id_default_image: int | None = None  # Default product image
    id_default_combination: int | None = None  # Default product combination
    reference: str | None = None
    name: str | None = None
    manufacturer_name: str | None = None
    price: str | None = None
    active: int | None = None
    date_add: str | None = None
    date_upd: str | None = None
    # Optional fields
    ean13: str | None = None
    isbn: str | None = None
    upc: str | None = None
    mpn: str | None = None
    supplier_reference: str | None = None
    location: str | None = None
    width: str | None = None
    height: str | None = None
    depth: str | None = None
    weight: str | None = None
    quantity: int | None = None
    description: str | None = None
    description_short: str | None = None
    available_for_order: int | None = None
    condition: str | None = None
    show_price: int | None = None
    indexed: int | None = None
    visibility: str | None = None
    cache_default_attribute: int | None = None
    advanced_stock_management: int | None = None
    available_date: str | None = None
    type: str | None = None
    state: int | None = None
    # Extra fields from API
    additional_shipping_cost: str | None = None
    ecotax: str | None = None
    link_rewrite: str | None = None
    meta_description: str | None = None
    meta_title: str | None = None  # Meta title for SEO
    minimal_quantity: int | None = None  # Minimum purchase quantity
    pack_stock_type: int | None = None  # Stock type for packs
    position_in_category: int | None = None
    product_type: str | None = None
    redirect_type: str | None = None  # Redirect type (404, etc)
    unit_price: str | None = None
    unit_price_ratio: str | None = None
    wholesale_price: str | None = None
    additional_delivery_times: int | None = None  # Delivery times option
    associations: dict[str, Any] | None = None
    cache_is_pack: int | None = None
    low_stock_threshold: int | None = None
    unity: str | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class AddressData:
    """Address resource data."""

    id: int
    # All fields optional except id
    id_customer: int | None = None
    id_country: int | None = None
    alias: str | None = None
    lastname: str | None = None
    firstname: str | None = None
    address1: str | None = None
    city: str | None = None
    postcode: str | None = None
    date_add: str | None = None
    date_upd: str | None = None
    id_manufacturer: int | None = None
    id_supplier: int | None = None
    id_warehouse: int | None = None
    id_state: int | None = None
    company: str | None = None
    vat_number: str | None = None
    address2: str | None = None
    phone: str | None = None
    phone_mobile: str | None = None
    dni: str | None = None
    deleted: int | None = None
    other: str | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class CountryData:
    """Country resource data."""

    id: int
    # All fields optional except id
    id_zone: int | None = None
    iso_code: str | None = None
    name: str | None = None
    active: int | None = None
    call_prefix: int | None = None
    contains_states: int | None = None
    need_identification_number: int | None = None
    need_zip_code: int | None = None
    zip_code_format: str | None = None
    display_tax_label: int | None = None
    id_currency: int | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class CarrierData:
    """Carrier resource data."""

    id: int
    deleted: int | None = None
    is_module: int | None = None
    id_tax_rules_group: int | None = None
    id_reference: int | None = None
    name: str | None = None
    active: int | None = None
    is_free: int | None = None
    url: str | None = None
    shipping_handling: int | None = None
    shipping_external: int | None = None
    range_behavior: int | None = None
    shipping_method: int | None = None
    max_width: int | None = None
    max_height: int | None = None
    max_depth: int | None = None
    max_weight: str | None = None
    grade: int | None = None
    external_module_name: str | None = None
    need_range: int | None = None
    position: int | None = None
    delay: str | dict[str, Any] | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class OrderCarrierData:
    """Order carrier resource data."""

    id: int
    # All fields optional except id
    id_order: int | None = None
    id_carrier: int | None = None
    id_order_invoice: int | None = None
    weight: str | None = None
    shipping_cost_tax_excl: str | None = None
    shipping_cost_tax_incl: str | None = None
    tracking_number: str | None = None
    date_add: str | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class OrderHistoryData:
    """Order history resource data."""

    id: int
    # All fields optional except id
    id_order: int | None = None
    id_order_state: int | None = None
    id_employee: int | None = None
    date_add: str | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class OrderStateData:
    """Order state resource data."""

    id: int
    # All fields optional except id
    name: str | None = None
    color: str | None = None
    unremovable: int | None = None
    send_email: int | None = None
    module_name: str | None = None
    invoice: int | None = None
    # Extra from API
    template: str | None = None
    # Fields that may not come
    deleted: int | None = None
    delivery: int | None = None
    hidden: int | None = None
    logable: int | None = None
    paid: int | None = None
    pdf_delivery: int | None = None
    pdf_invoice: int | None = None
    shipped: int | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class StateData:
    """State/Province resource data."""

    id: int
    # All fields optional except id
    id_country: int | None = None
    id_zone: int | None = None
    name: str | None = None
    iso_code: str | None = None
    active: int | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class ImageProductData:
    """Product image resource data."""

    id: int
    # All fields optional except id
    id_product: int | None = None
    position: int | None = None
    cover: int | None = None
    legend: str | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass


@dataclass
class CombinationData:
    """Combination resource data."""

    id: int
    # All fields optional except id
    id_product: int | None = None
    ean13: str | None = None
    reference: str | None = None
    wholesale_price: str | None = None
    price: str | None = None
    ecotax: str | None = None
    weight: str | None = None
    unit_price_impact: str | None = None
    minimal_quantity: int | None = None
    low_stock_threshold: int | None = None
    default_on: int | None = None
    available_date: str | None = None
    associations: dict[str, Any] | None = None

    def __post_init__(self, **kwargs):
        """Ignore extra fields from API."""
        pass
