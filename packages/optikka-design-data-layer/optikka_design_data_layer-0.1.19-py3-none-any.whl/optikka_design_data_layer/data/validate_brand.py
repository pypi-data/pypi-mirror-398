"""
Validate a brand against a brand registry.
"""
import math
from datetime import datetime
from optikka_design_data_layer import logger
from ods_models import Brand, BrandRegistry, EntityAttributeSpec, BrandWithoutId, DataType
from optikka_design_data_layer.data.validate_template_input_object import InputObjectValidationResult, InputObjectValidationError
from optikka_design_data_layer.db.mongo_client import mongodb_client

class BrandValidator:
    """
    Validate a brand.
    """
    def __init__(
        self,
        brand: Brand | BrandWithoutId | None = None,
        brand_registry: BrandRegistry | None = None,
        brand_id: str | None = None,
    ):
        """
        Initialize the brand validator.
        """
        self.brand = brand
        self.brand_id = brand_id
        self.brand_registry: BrandRegistry = brand_registry
        if self.brand_id is None and self.brand is None:
            raise ValueError("Brand id is required")
        if self.brand_id is not None and self.brand is not None:
            raise ValueError("Brand id and brand are mutually exclusive")
        if self.brand_id is None and self.brand is not None and not isinstance(self.brand, BrandWithoutId):
            logger.debug(f"Setting brand id from brand: {self.brand.id}")
            self.brand_id = self.brand.id

    def setup(self) -> None:
        """
        Setup the brand validator.
        """
        if self.brand is None:
            self._load_brand(self.brand_id)
        if self.brand is None:
            raise ValueError("Brand not found")
        if self.brand_registry is None:
            self._load_brand_registry(self.brand.brand_registry_id)
        if self.brand_registry is None:
            raise ValueError("Brand registry not found")

    #basic setters#
    def set_brand_registry(self, brand_registry: BrandRegistry) -> None:
        """
        Set the brand registry.
        """
        self.brand_registry = brand_registry

    def set_brand_registry_by_id(self, brand_registry_id: str) -> None:
        """
        Set the brand registry by id.
        """
        self.brand_registry = mongodb_client.get_brand_registry_by_id(brand_registry_id)
        if self.brand_registry is None:
            raise ValueError("Brand registry not found")

    def set_brand(self, brand: Brand) -> None:
        """
        Set the brand.
        """
        self.brand = brand

    def set_brand_by_id(self, brand_id: str) -> None:
        """
        Set the brand by id.
        """
        brand_dict = mongodb_client.get_brand_by_id(brand_id)
        if brand_dict is None:
            raise ValueError("Brand not found")
        brand_dict["id"] = str(brand_dict["_id"])
        del brand_dict["_id"]
        self.brand = Brand(**brand_dict)
        if self.brand is None:
            raise ValueError("Brand not found")

    def _load_brand_registry(self, brand_registry_id: str) -> None:
        """
        Load the brand registry.
        """
        brand_registry_dict = mongodb_client.get_brand_registry_by_id(brand_registry_id)
        if brand_registry_dict is None:
            raise ValueError("Brand registry not found")
        brand_registry_dict["id"] = str(brand_registry_dict["_id"])
        del brand_registry_dict["_id"]
        self.brand_registry = BrandRegistry(**brand_registry_dict)
        if self.brand_registry is None:
            raise ValueError("Brand registry not found")

    def _load_brand(self, brand_id: str) -> None:
        """
        Load the brand.
        """
        brand_dict = mongodb_client.get_brand_by_id(brand_id)
        brand_dict["id"] = str(brand_dict["_id"])
        del brand_dict["_id"]
        self.brand = Brand(**brand_dict)
        if self.brand is None:
            raise ValueError("Brand not found")
    #end basic setters#

    #utils methods#
    def _validate_image(self, image_key: str, image_value) -> InputObjectValidationError | None:
        """
        Validate the image.
        """
        if image_value is None or image_value == "" or image_value == "null":
            return InputObjectValidationError(
                f"Brand image {image_key} is required but missing from the brand."
            )
        return None

    def _validate_images(self) -> InputObjectValidationResult:
        """
        Validate the images.
        """
        validation_result = InputObjectValidationResult(is_valid=True, errors=[])
        for image_key in self.brand_registry.required_images.keys():
            if image_key not in self.brand.images.keys():
                validation_result.is_valid = False
                validation_result.errors.append(
                    InputObjectValidationError(
                        f"Brand image {image_key} is required but missing from the brand."
                    )
                )
                continue
            image_value = self.brand.images.get(image_key)
            validation_error = self._validate_image(image_key, image_value)
            if validation_error is not None:
                validation_result.is_valid = False
                validation_result.errors.append(validation_error)
                continue

        for image_key in self.brand.images.keys():
            if image_key not in self.brand_registry.required_images.keys():
                validation_result.is_valid = False
                validation_result.errors.append(InputObjectValidationError(
                    f"Brand image {image_key} is not in the brand registry.")
                )
                continue
        return validation_result

    def _validate_attribute(
        self,
        attribute_spec: EntityAttributeSpec,
        attribute_value
    ) -> InputObjectValidationError | None:
        """
        Validate the attribute.
        Returns InputObjectValidationError if validation fails, None if successful.
        """

        try:
            if attribute_spec.type == DataType.STRING:
                # Convert to string - this should always work
                if attribute_value is None:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} cannot be None for STRING type."
                    )
                str(attribute_value)  # Validate it can be converted

            elif attribute_spec.type == DataType.NUMBER:
                # Validate and convert to number
                if attribute_value is None or attribute_value == "":
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} cannot be None or empty for NUMBER type."
                    )
                try:
                    num_value = float(attribute_value)
                    # Check for NaN, Infinity, or -Infinity
                    if math.isnan(num_value):
                        return InputObjectValidationError(
                            f"Brand attribute {attribute_spec.name} is NaN (Not a Number)."
                        )
                    if math.isinf(num_value):
                        return InputObjectValidationError(
                            f"Brand attribute {attribute_spec.name} is Infinity or -Infinity."
                        )
                except (ValueError, TypeError) as e:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid number: {e}"
                    )

            elif attribute_spec.type == DataType.BOOLEAN:
                if isinstance(attribute_value, bool):
                    # Already a boolean, use as-is
                    pass
                elif isinstance(attribute_value, str):
                    # Handle string representations
                    if attribute_value.lower() == "true":
                        pass  # Valid
                    elif attribute_value.lower() == "false":
                        pass  # Valid
                    else:
                        return InputObjectValidationError(
                            f"Brand attribute {attribute_spec.name} is not a valid boolean (expected 'true' or 'false', got '{attribute_value}')."
                        )
                else:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid boolean (expected bool or string 'true'/'false', got {type(attribute_value).__name__})."
                    )

            elif attribute_spec.type == DataType.DATE:
                if attribute_value is None or not isinstance(attribute_value, str):
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} must be a string for DATE type."
                    )
                try:
                    datetime.strptime(attribute_value, "%Y-%m-%d")
                except ValueError as e:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid DATE (expected format: YYYY-MM-DD, got '{attribute_value}'): {e}"
                    )

            elif attribute_spec.type == DataType.TIME:
                if attribute_value is None or not isinstance(attribute_value, str):
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} must be a string for TIME type."
                    )
                try:
                    datetime.strptime(attribute_value, "%H:%M:%S")
                except ValueError as e:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid TIME (expected format: HH:MM:SS, got '{attribute_value}'): {e}"
                    )

            elif attribute_spec.type == DataType.DATETIME:
                if attribute_value is None or not isinstance(attribute_value, str):
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} must be a string for DATETIME type."
                    )
                try:
                    datetime.strptime(attribute_value, "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid DATETIME (expected format: YYYY-MM-DD HH:MM:SS, got '{attribute_value}'): {e}"
                    )

            elif attribute_spec.type == DataType.ENUM:
                if attribute_spec.allowed_values is None or len(attribute_spec.allowed_values) == 0:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is ENUM type but has no allowed_values defined."
                    )
                if attribute_value not in attribute_spec.allowed_values and attribute_spec.allowed_values is not None and len(attribute_spec.allowed_values) > 0:
                    return InputObjectValidationError(
                        f"Brand attribute {attribute_spec.name} is not a valid enum value. Allowed values: {attribute_spec.allowed_values}, got: '{attribute_value}'"
                    )
            else:
                return InputObjectValidationError(
                    f"Brand attribute {attribute_spec.name} has unknown type: {attribute_spec.type}"
                )

            # Validation passed
            return None

        except Exception as e:#pylint: disable=broad-exception-caught
            return InputObjectValidationError(
                f"Error validating attribute {attribute_spec.name}: {e}"
            )

    def _validate_studio_and_account(self) -> InputObjectValidationResult:
        """
        Validate the studio and account.
        """
        if self.brand_registry.is_universal:
            return InputObjectValidationResult(is_valid=True, errors=[])
        if self.brand.is_universal and not self.brand_registry.is_universal:
            return InputObjectValidationResult(is_valid=False, errors=[
                InputObjectValidationError(
                    f"Brand is universal but brand registry is not."
                )
            ])
        validation_result = InputObjectValidationResult(is_valid=True, errors=[])

        # Check if any brand studio_id is not in the registry
        missing_studio_ids = set(self.brand.studio_ids) - set(self.brand_registry.studio_ids)
        if missing_studio_ids:
            validation_result.is_valid = False
            validation_result.errors.append(
                InputObjectValidationError(
                    f"Brand studio ids {list(missing_studio_ids)} are not in brand registry studio ids {self.brand_registry.studio_ids}"
                )
            )
        # Check if any brand account_id is not in the registry
        missing_account_ids = set(self.brand.account_ids) - set(self.brand_registry.account_ids)
        if missing_account_ids:
            validation_result.is_valid = False
            validation_result.errors.append(
                InputObjectValidationError(
                    f"Brand account ids {list(missing_account_ids)} are not in brand registry account ids {self.brand_registry.account_ids}"
                )
            )
        return validation_result

    #core methods#

    def validate_full(self) -> InputObjectValidationResult:
        """
        Validate the brand fully.
        """
        validation_result = InputObjectValidationResult(is_valid=True, errors=[])
        validate_just_attributes_result = self.validate_just_attributes_and_studio_and_account()

        # Merge results
        if not validate_just_attributes_result.is_valid:
            validation_result.is_valid = False
            validation_result.errors.extend(validate_just_attributes_result.errors)

        #Images validation starts here
        validate_images_result = self._validate_images()
        if not validate_images_result.is_valid:
            validation_result.is_valid = False
            validation_result.errors.extend(validate_images_result.errors)

        #Studio and account validation starts here
        validate_studio_and_account_result = self._validate_studio_and_account()
        if not validate_studio_and_account_result.is_valid:
            validation_result.is_valid = False
            validation_result.errors.extend(validate_studio_and_account_result.errors)

        return validation_result

    def validate_just_attributes_and_studio_and_account(self) -> InputObjectValidationResult:
        """
        Validate the brand just the attributes.
        """
        validation_result = InputObjectValidationResult(is_valid=True, errors=[])

        for attribute_spec_key in self.brand_registry.entity_attributes_specs.keys():
            attribute_spec = self.brand_registry.entity_attributes_specs.get(attribute_spec_key)
            if attribute_spec is None:
                continue
            if attribute_spec.required:
                #it is required and we need it
                if attribute_spec_key not in self.brand.entity_attributes.keys():
                    #if it is required and not in the brand, it is invalid
                    validation_result.is_valid = False
                    validation_result.errors.append(
                        InputObjectValidationError(
                            f"Brand attribute {attribute_spec.name} is required but missing from the brand."
                        )
                    )
                    continue
                if self.brand.entity_attributes[attribute_spec_key] is None:
                    #if it is there and we need it but is None, it is invalid
                    validation_result.is_valid = False
                    validation_result.errors.append(
                        InputObjectValidationError(
                            f"Brand attribute {attribute_spec.name} is required but is None."
                        )
                    )
                    continue
            else:
                if attribute_spec_key not in self.brand.entity_attributes.keys() or self.brand.entity_attributes[attribute_spec_key] is None:
                    #if it is not required and not in the brand or is None, it is valid
                    continue

            #finally we defs have the attribute and whether we need it or not, we need to validate it
            validation_error = self._validate_attribute(
                attribute_spec,
                self.brand.entity_attributes.get(attribute_spec_key)
            )
            if validation_error is not None:
                validation_result.is_valid = False
                validation_result.errors.append(validation_error)

        #finally we need to check that there are no extra attributes in the brand that are not in the brand registry
        for attribute_key in self.brand.entity_attributes.keys():
            if attribute_key not in self.brand_registry.entity_attributes_specs.keys():
                validation_result.is_valid = False
                validation_result.errors.append(
                    InputObjectValidationError(
                        f"Brand attribute {attribute_key} is not in the brand registry."
                    )
                )
        
        validate_studio_and_account_result = self._validate_studio_and_account()
        if not validate_studio_and_account_result.is_valid:
            validation_result.errors.extend(validate_studio_and_account_result.errors)

        return validation_result

    #MAIN METHOD
    def validate(self, validate_full: bool = True) -> InputObjectValidationResult:
        """
        Validate the brand.
        """
        self.setup()
        if validate_full:
            logger.debug("Validating brand fully")
            return self.validate_full()
        logger.debug("Validating brand just the attributes")
        return self.validate_just_attributes_and_studio_and_account()
