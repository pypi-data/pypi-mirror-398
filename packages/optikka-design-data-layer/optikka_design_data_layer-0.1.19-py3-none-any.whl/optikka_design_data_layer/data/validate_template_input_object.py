"""
Validate the template input object.
"""

from typing import List
from optikka_design_data_layer.db.mongo_client import mongodb_client
from ods_models import (
    TemplateInput,
    TemplateRegistry,
    DesignDataInputTypes,
    AssetSpecs,
    LogoSpecs,
    TextSpecs,
    TextType,
    GuideDoc,
)


class InputObjectValidationError(Exception):
    """
    Error for input object validation.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InputObjectValidationResult:
    """
    Result of the input object validation.
    """

    def __init__(self, is_valid: bool, errors: List[InputObjectValidationError]):
        self.is_valid = is_valid
        self.errors = errors


class TemplateInputValidator:  # pylint: disable=too-many-instance-attributes
    """
    Validate the template input object.
    """

    def __init__(
        self,
        template_registry: TemplateRegistry | None = None,
        template_input: TemplateInput | None = None,
    ):
        # Initialize instance variables (fresh for each instance)
        self.template_registry: TemplateRegistry | None = template_registry
        self.template_input: TemplateInput | None = template_input

        # registry dicts
        self.registry_assets_dict: dict = {}
        self.registry_logos_dict: dict = {}
        self.registry_texts_dict: dict = {}
        self.registry_extra_data_dict: dict = {}
        self.registry_inputs_dict: dict = {}

        # input dicts
        self.input_assets_dict: dict = {}
        self.input_logos_dict: dict = {}
        self.input_texts_dict: dict = {}
        self.input_extra_data_dict: dict = {}
        self.input_dict: dict = {}

        # errors
        self.errors: List[InputObjectValidationError] = []

        # Set the inputs
        self.set_template_registry(template_registry)
        self.set_template_input(template_input)

        self.registry_inputs_dict: dict = {
            DesignDataInputTypes.ASSETS.value: self.registry_assets_dict,
            DesignDataInputTypes.LOGOS.value: self.registry_logos_dict,
            DesignDataInputTypes.TEXTS.value: self.registry_texts_dict,
            DesignDataInputTypes.EXTRA_DATA.value: self.registry_extra_data_dict,
        }

        self.input_dict: dict = {
            DesignDataInputTypes.ASSETS.value: self.input_assets_dict,
            DesignDataInputTypes.LOGOS.value: self.input_logos_dict,
            DesignDataInputTypes.TEXTS.value: self.input_texts_dict,
            DesignDataInputTypes.EXTRA_DATA.value: self.input_extra_data_dict,
        }

    # SETTERS#
    def set_template_registry(self, template_registry: TemplateRegistry):
        """
        Set the template registry.
        """
        self.template_registry = template_registry

    def set_template_registry_by_id(self, template_registry_id: str):
        """
        Set the template registry by id.
        """
        template_registry_dict = mongodb_client.get_template_registry_by_id(
            template_registry_id
        )
        template_registry_dict["id"] = str(template_registry_dict["_id"])
        del template_registry_dict["_id"]
        self.template_registry = TemplateRegistry(**template_registry_dict)
        if self.template_registry is None:
            raise InputObjectValidationError(
                f"Template registry with id {template_registry_id} not found"
            )

    def set_template_input(self, template_input: TemplateInput):
        """
        Set the template input.
        """
        self.template_input = template_input

    def set_template_input_by_id(self, template_input_id: str):
        """
        Set the template input by id.
        """
        template_input_dict = mongodb_client.get_template_input_by_id(template_input_id)
        template_input_dict["id"] = str(template_input_dict["_id"])
        del template_input_dict["_id"]
        self.template_input = TemplateInput(**template_input_dict)
        if self.template_input is None:
            raise InputObjectValidationError(
                f"Template input with id {template_input_id} not found"
            )

    def clear_state(self):
        """
        Clear all state for fresh validation.
        """
        self.registry_assets_dict.clear()
        self.registry_logos_dict.clear()
        self.registry_texts_dict.clear()
        self.registry_extra_data_dict.clear()
        self.registry_inputs_dict.clear()

        self.input_assets_dict.clear()
        self.input_logos_dict.clear()
        self.input_texts_dict.clear()
        self.input_extra_data_dict.clear()
        self.input_dict.clear()

        self.errors.clear()

    # MAIN METHODS#
    def validate(self) -> InputObjectValidationResult:
        """
        Validate the template input object.
        """
        try:

            # these errors are not recoverable
            if self.template_registry is None:
                raise InputObjectValidationError("Template registry is not set")
            if self.template_input is None:
                raise InputObjectValidationError("Template input is not set")

            # make sure the account and studio are valid according to the template registry
            self._validate_studio_and_account()

            # convert the input arrays and registry input arrays to dicts for faster lookup
            self._convert_input_arrays_to_dicts()
            self._convert_registry_input_arrays_to_dicts()

            # make sure the assets are valid according to the template registry
            self._validate_assets()

            # make sure the logos are valid according to the template registry
            self._validate_logos()

            # make sure the text values are valid according to the template registry
            self._validate_texts()

            # make sure the groups are valid according to the template registry
            self._validate_groups()

            # make sure the extra data is valid according to the template registry
            self._validate_extra_data()

            # validate canvas key
            if self.template_input.canvas_key is not None:
                self._validate_canvas_key()

        except InputObjectValidationError as e:
            self.errors.append(e)
        except (
            Exception
        ) as e:  # for none recoverable errors, we want to handle error at api level
            raise e
        return self._get_result()

    def _get_result(self) -> InputObjectValidationResult:
        """
        Get the result.
        """
        return InputObjectValidationResult(
            is_valid=len(self.errors) == 0, errors=self.errors
        )

    # STUDIO AND ACCOUNT VALIDATION METHODS#
    def _validate_studio_and_account(self) -> bool:
        """
        Validate the studio and account.
        """
        if self.template_input.studio_id not in self.template_registry.studio_ids:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input studio id {self.template_input.studio_id} not in template registry studio ids {self.template_registry.studio_ids}"
                )
            )
        if self.template_input.account_id not in self.template_registry.account_ids:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input account id {self.template_input.account_id} not in template registry account ids {self.template_registry.account_ids}"
                )
            )

    # CONVERT METHODS#
    def _convert_registry_input_arrays_to_dicts(self) -> dict:
        """
        Convert the input arrays to dicts.
        """
        if (
            hasattr(self.template_registry.input_parameters, "assets")
            and self.template_registry.input_parameters.assets
        ):
            for asset in self.template_registry.input_parameters.assets:
                self.registry_assets_dict[asset.parsing_label] = asset
        if (
            hasattr(self.template_registry.input_parameters, "logos")
            and self.template_registry.input_parameters.logos
        ):
            for logo in self.template_registry.input_parameters.logos:
                self.registry_logos_dict[logo.parsing_label] = logo
        if (
            hasattr(self.template_registry.input_parameters, "texts")
            and self.template_registry.input_parameters.texts
        ):
            for text in self.template_registry.input_parameters.texts:
                self.registry_texts_dict[text.parsing_label] = text
        if (
            hasattr(self.template_registry.input_parameters, "extra_data")
            and self.template_registry.input_parameters.extra_data
        ):
            self.registry_extra_data_dict = (
                self.template_registry.input_parameters.extra_data
            )
        else:
            self.registry_extra_data_dict = {}

    def _convert_input_arrays_to_dicts(self) -> dict:
        """
        Convert the input arrays to dicts.
        Note: Multiple items with the same parsing_label are now allowed (for 1:many support).
        When duplicates exist, we store them as a list. Otherwise, store as a single item.
        """
        if (
            hasattr(self.template_input.inputs, "assets")
            and self.template_input.inputs.assets
        ):
            for asset in self.template_input.inputs.assets:
                existing = self.input_assets_dict.get(asset.parsing_label)
                if existing is None:
                    self.input_assets_dict[asset.parsing_label] = asset
                elif isinstance(existing, list):
                    existing.append(asset)
                else:
                    self.input_assets_dict[asset.parsing_label] = [existing, asset]
        if (
            hasattr(self.template_input.inputs, "logos")
            and self.template_input.inputs.logos
        ):
            for logo in self.template_input.inputs.logos:
                existing = self.input_logos_dict.get(logo.parsing_label)
                if existing is None:
                    self.input_logos_dict[logo.parsing_label] = logo
                elif isinstance(existing, list):
                    existing.append(logo)
                else:
                    self.input_logos_dict[logo.parsing_label] = [existing, logo]
        if (
            hasattr(self.template_input.inputs, "texts")
            and self.template_input.inputs.texts
        ):
            for text in self.template_input.inputs.texts:
                existing = self.input_texts_dict.get(text.parsing_label)
                if existing is None:
                    self.input_texts_dict[text.parsing_label] = text
                elif isinstance(existing, list):
                    existing.append(text)
                else:
                    self.input_texts_dict[text.parsing_label] = [existing, text]
        
        if (
            hasattr(self.template_input.inputs, "groups")
            and self.template_input.inputs.groups
        ):
            group = self.template_input.inputs.groups
            # Items in groups use the group's parsing_label, not their own
            group_parsing_label = group.parsing_label if hasattr(group, 'parsing_label') else None
            if group_parsing_label:
                for item in group.items:
                    # Groups only support Asset and Logo items, not Text items
                    # Check if item is a Text by checking type attribute or value attribute without s3Location
                    item_type = getattr(item, 'type', None)
                    is_text = (
                        item_type == 'text' or 
                        (hasattr(item, 'value') and not hasattr(item, 's3Location'))
                    )
                    
                    if is_text:
                        # Text items are not allowed in groups
                        self.errors.append(
                            InputObjectValidationError(
                                f"Text items are not allowed in groups. Group '{group_parsing_label}' contains a text item. Text items must be in the 'texts' array with their own parsing_label."
                            )
                        )
                        continue
                    
                    if hasattr(item, 's3Location'):
                        if hasattr(item, 'workflow_registry_id') or hasattr(item, 'workflow_registry_ids'):
                            # Logo
                            existing = self.input_logos_dict.get(group_parsing_label)
                            if existing is None:
                                self.input_logos_dict[group_parsing_label] = item
                            elif isinstance(existing, list):
                                existing.append(item)
                            else:
                                self.input_logos_dict[group_parsing_label] = [existing, item]
                        else:
                            # Asset
                            existing = self.input_assets_dict.get(group_parsing_label)
                            if existing is None:
                                self.input_assets_dict[group_parsing_label] = item
                            elif isinstance(existing, list):
                                existing.append(item)
                            else:
                                self.input_assets_dict[group_parsing_label] = [existing, item]
        
        if (
            hasattr(self.template_input.inputs, "extra_data")
            and self.template_input.inputs.extra_data
        ):
            self.input_extra_data_dict = self.template_input.inputs.extra_data
        else:
            self.input_extra_data_dict = {}

    # GENERAL VALIDATION METHODS#
    def _validate_counts(self, input_type: DesignDataInputTypes) -> bool:
        """
        Validate the counts.
        """
        input_type_str = input_type.value
        input_array = self.input_dict[input_type_str]
        count = len(getattr(self.template_registry.input_parameters, input_type_str))

        if count > 0:
            if len(input_array) != count:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input {input_type_str} count {len(input_array)} does not match template registry {count}"
                    )
                )
        if count == 0:
            if len(input_array) > 0:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input {input_type_str} count {len(input_array)} does not match template registry {count}"
                    )
                )

    def _validate_key_matches_for_a_type(
        self, input_type: DesignDataInputTypes
    ) -> bool:
        """
        Check for matches.
        Respects the 'optional' field - missing inputs are allowed if optional=True.
        """
        additonal_value_keys = []
        missing_value_keys = []
        duplicate_input_keys = []
        input_type_str = input_type.value
        # check for additional inputs from template input
        for input_key in self.input_dict[input_type_str].keys():
            registry_input_for_type = self.registry_inputs_dict[input_type_str]
            if registry_input_for_type.get(input_key) is None:
                additonal_value_keys.append(input_key)

        # check for missing inputs from registry def
        for key in self.registry_inputs_dict[input_type_str].keys():
            if self.input_dict[input_type_str].get(key) is None:
                # Check if this input is optional
                spec = self.registry_inputs_dict[input_type_str].get(key)
                is_optional = getattr(spec, 'optional', False)
                if not is_optional:
                    missing_value_keys.append(key)

        if len(missing_value_keys) > 0:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input {missing_value_keys} not found in template registry {input_type_str}"
                )
            )
        if len(additonal_value_keys) > 0:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input {additonal_value_keys} found in template registry {input_type_str} but not in template input"
                )
            )
        if len(duplicate_input_keys) > 0:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input {duplicate_input_keys} found in template input but not in template registry {input_type_str}"
                )
            )

    # ASSET VALIDATION METHODS#
    def _validate_guides_schema(
        self, input_guides: list[GuideDoc], guides_required: list[str]
    ):
        """
        Validate the guides schema.
        """

        all_guide_names_in_input = []
        for guide in input_guides:
            all_guide_names_in_input.append(guide.name)
        for guide_required in guides_required:
            if guide_required not in all_guide_names_in_input:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template asset specs guide name: {guide_required} not in supplied input guides: {all_guide_names_in_input}"
                    )
                )

    def _validate_asset_or_logo_value(
        self, asset_value: dict, template_asset_defintion: AssetSpecs, parsing_label: str = None
    ):
        """
        Validate the asset value.
        parsing_label: Optional parsing label to use in error messages (for group items that don't have parsing_label).
        Respects the 'validate' field - skips dimension/type validation if validate=False.
        """
        # Use provided parsing_label or fall back to asset_value.parsing_label if it exists
        label = parsing_label if parsing_label is not None else getattr(asset_value, 'parsing_label', template_asset_defintion.parsing_label)

        # Check if validation is enabled for this spec (default: True)
        # Support both 'validate' (old) and 'should_validate' (new) field names for backward compatibility
        should_validate = getattr(template_asset_defintion, 'should_validate', getattr(template_asset_defintion, 'validate', True))

        if not should_validate:
            # Skip dimension/type validation if validate=False
            return

        allowed_mime_types = template_asset_defintion.allowed_types

        if asset_value.mime_type not in allowed_mime_types:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input asset: {label}'s mime type: {str(asset_value.mime_type)} not in allowed mime types {[str(mime_type) for mime_type in allowed_mime_types]} for that asset / logo."
                )
            )
        if asset_value.width < template_asset_defintion.min_width:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input asset: {label}'s width: {asset_value.width} is less than the minimum width: {template_asset_defintion.min_width}"
                )
            )
        if asset_value.height < template_asset_defintion.min_height:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input asset: {label}'s height: {asset_value.height} is less than the minimum height: {template_asset_defintion.min_height}"
                )
            )
        if asset_value.width > template_asset_defintion.max_width:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input asset: {label}'s width: {asset_value.width} is greater than the maximum width: {template_asset_defintion.max_width}"
                )
            )
        if asset_value.height > template_asset_defintion.max_height:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input asset: {label}'s height: {asset_value.height} is greater than the maximum height: {template_asset_defintion.max_height}"
                )
            )
        if template_asset_defintion.guides_required is not None:
            self._validate_guides_schema(
                asset_value.guides, template_asset_defintion.guides_required
            )
        if (
            template_asset_defintion.workflow_registry_id is not None
            and template_asset_defintion.workflow_required
        ):
            if asset_value.workflow_registry_id is None:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input asset {asset_value.workflow_registry_id} not in allowed workflow registry id {template_asset_defintion.workflow_registry_id}"
                    )
                )
            elif (
                asset_value.workflow_registry_id
                != template_asset_defintion.workflow_registry_id
            ):
                label = parsing_label if parsing_label is not None else getattr(asset_value, 'parsing_label', template_asset_defintion.parsing_label)
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input asset {label} workflow registry id {asset_value.workflow_registry_id} does not match template registry {template_asset_defintion.workflow_registry_id}"
                    )
                )

    def _validate_all_asset_values(self):
        """
        Validate the values.
        Supports both single items and arrays (for 1:many support).
        """
        input_assets = self.input_dict[DesignDataInputTypes.ASSETS.value]
        template_asset_defintions = self.registry_inputs_dict[
            DesignDataInputTypes.ASSETS.value
        ]
        for input_asset_key in input_assets.keys():
            input_asset_value = input_assets.get(input_asset_key)
            template_asset_defintion = template_asset_defintions.get(input_asset_key)
            if template_asset_defintion is None:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input asset {input_asset_key} not in template registry {DesignDataInputTypes.ASSETS.value}"
                    )
                )
                continue
            
            # Handle arrays (multiple items with same parsing_label)
            if isinstance(input_asset_value, list):
                for asset_item in input_asset_value:
                    self._validate_asset_or_logo_value(
                        asset_item, template_asset_defintion, parsing_label=input_asset_key
                    )
            else:
                # Single item
                self._validate_asset_or_logo_value(
                    input_asset_value, template_asset_defintion, parsing_label=input_asset_key
                )

    def _validate_assets(self):
        """
        Validate the assets match the template registry.
        """

        # validate the counts
        self._validate_counts(DesignDataInputTypes.ASSETS)
        # validate the keys match
        self._validate_key_matches_for_a_type(DesignDataInputTypes.ASSETS)
        # validate the values for each asset against its defintion
        self._validate_all_asset_values()

    # LOGOS VALIDATION METHODS#
    def _validate_logo_value(
        self, logo_value: dict, template_logo_defintion: LogoSpecs
    ):
        """
        Validate the logo value.
        """
        if logo_value.get("mimeType") not in template_logo_defintion.allowed_types:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input logo {logo_value.get('mimeType')} not in allowed mime types {template_logo_defintion.allowed_types}"
                )
            )
        if logo_value.get("width") < template_logo_defintion.min_width:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input logo {logo_value.get('width')} not in allowed width {template_logo_defintion.min_width}"
                )
            )
        if logo_value.get("height") < template_logo_defintion.min_height:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input logo {logo_value.get('height')} not in allowed height {template_logo_defintion.min_height}"
                )
            )
        if logo_value.get("width") > template_logo_defintion.max_width:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input logo {logo_value.get('width')} not in allowed width {template_logo_defintion.max_width}"
                )
            )
        if logo_value.get("height") > template_logo_defintion.max_height:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input logo {logo_value.get('height')} not in allowed height {template_logo_defintion.max_height}"
                )
            )
        if template_logo_defintion.guides_required is not None:
            self._validate_guides_schema(
                logo_value.guides, template_logo_defintion.guides_required
            )
        if (
            template_logo_defintion.workflow_registry_id is not None
            and template_logo_defintion.workflow_required
        ):
            if logo_value.get("workflowRegistryId") is None:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input logo {logo_value.get('workflowRegistryId')} not in allowed workflow registry id {template_logo_defintion.workflow_registry_id}"
                    )
                )
            elif (
                logo_value.get("workflowRegistryId")
                != template_logo_defintion.workflow_registry_id
            ):
                # Note: logo_value might be a dict from MongoDB, so use get() with fallback
                logo_label = logo_value.get('parsing_label', template_logo_defintion.parsing_label)
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input logo {logo_label} workflow registry id {logo_value.get('workflowRegistryId')} does not match template registry {template_logo_defintion.workflow_registry_id}"
                    )
                )

    def _validate_all_logo_values(self):
        """
        Validate the values.
        Supports both single items and arrays (for 1:many support).
        """
        input_logos = self.input_dict[DesignDataInputTypes.LOGOS.value]
        template_logo_defintions = self.registry_inputs_dict[
            DesignDataInputTypes.LOGOS.value
        ]
        for input_logo_key in input_logos.keys():
            input_logo_value = input_logos.get(input_logo_key)
            template_logo_defintion = template_logo_defintions.get(input_logo_key)
            if template_logo_defintion is None:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input logo {input_logo_key} not in template registry {DesignDataInputTypes.LOGOS.value}"
                    )
                )
                continue
            
            # Handle arrays (multiple items with same parsing_label)
            if isinstance(input_logo_value, list):
                for logo_item in input_logo_value:
                    self._validate_asset_or_logo_value(
                        logo_item, template_logo_defintion, parsing_label=input_logo_key
                    )
            else:
                # Single item
                self._validate_asset_or_logo_value(
                    input_logo_value, template_logo_defintion, parsing_label=input_logo_key
                )

    def _validate_logos(self):
        """
        Validate the logos.
        """
        self._validate_counts(DesignDataInputTypes.LOGOS)
        self._validate_key_matches_for_a_type(DesignDataInputTypes.LOGOS)
        self._validate_all_logo_values()

    # TEXT VALIDATION METHODS#
    def _validate_text_value(
        self, text_value: dict, template_text_defintion: TextSpecs, parsing_label: str = None
    ):
        """
        Validate the text value.
        parsing_label: Optional parsing label to use in error messages (for group items that don't have parsing_label).
        Respects the 'validate' field - skips char limit/type validation if validate=False.
        """
        # Use provided parsing_label or fall back to text_value.parsing_label if it exists
        label = parsing_label if parsing_label is not None else getattr(text_value, 'parsing_label', template_text_defintion.parsing_label)

        # Check if validation is enabled for this spec (default: True)
        # Support both 'validate' (old) and 'should_validate' (new) field names for backward compatibility
        should_validate = getattr(template_text_defintion, 'should_validate', getattr(template_text_defintion, 'validate', True))

        if not should_validate:
            # Skip char limit/type validation if validate=False
            return

        body = text_value.value
        if body is None:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input text {text_value.value} is None"
                )
            )
        if len(body) < template_text_defintion.min_chars:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input text: {label}'s value: {text_value.value} is less than {template_text_defintion.min_chars} characters"
                )
            )
        if len(body) > template_text_defintion.max_chars:
            self.errors.append(
                InputObjectValidationError(
                    f"Template input text: {label}'s value: {text_value.value} is greater than {template_text_defintion.max_chars} characters"
                )
            )

        text_type = template_text_defintion.type
        if text_type == TextType.SELECT:
            if (
                template_text_defintion.options is not None
                and len(template_text_defintion.options) > 0
            ):
                if body not in template_text_defintion.options:
                    self.errors.append(
                        InputObjectValidationError(
                            f"Template input text: {text_value.parsing_label}'s value: {text_value.value} not in allowed options {template_text_defintion.options}"
                        )
                    )
        elif text_type == TextType.NUMBER:
            try:
                float(body)
            except ValueError:
                self.errors.append(
                    InputObjectValidationError(
                        f"Could not convert template input text: {text_value.parsing_label}'s value: {text_value.value} to a number when type is {text_type}"
                    )
                )

    def _validate_all_text_values(self):
        """
        Validate the values.
        """
        input_texts = self.input_dict[DesignDataInputTypes.TEXTS.value]
        template_text_defintions = self.registry_inputs_dict[
            DesignDataInputTypes.TEXTS.value
        ]
        for input_text_key in input_texts.keys():
            input_text_value = input_texts.get(input_text_key)
            template_text_defintion = template_text_defintions.get(input_text_key)
            if template_text_defintion is None:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input text {input_text_key} not in template registry {DesignDataInputTypes.TEXTS.value}"
                    )
                )
                continue
            
            # Handle arrays (multiple items with same parsing_label)
            if isinstance(input_text_value, list):
                for text_item in input_text_value:
                    self._validate_text_value(text_item, template_text_defintion, parsing_label=input_text_key)
            else:
                # Single item
                self._validate_text_value(input_text_value, template_text_defintion, parsing_label=input_text_key)

    def _validate_texts(self):
        """
        Validate the texts.
        """
        self._validate_counts(DesignDataInputTypes.TEXTS)
        self._validate_key_matches_for_a_type(DesignDataInputTypes.TEXTS)
        self._validate_all_text_values()

    def _validate_groups(self):
        """
        Validate the groups.
        Respects the 'optional' field - missing groups are allowed if optional=True.
        """
        # Get group from template input (single optional group)
        input_group = None
        if (
            hasattr(self.template_input.inputs, "groups")
            and self.template_input.inputs.groups
        ):
            input_group = self.template_input.inputs.groups

        # Get groups from template registry (array of group specs)
        registry_groups = {}
        if (
            hasattr(self.template_registry.input_parameters, "groups")
            and self.template_registry.input_parameters.groups
        ):
            for group_spec in self.template_registry.input_parameters.groups:
                registry_groups[group_spec.parsing_label] = group_spec

        # Check if input has group when registry doesn't
        if len(registry_groups) == 0 and input_group is not None:
            self.errors.append(
                InputObjectValidationError(
                    "Template registry does not define groups but template input has a group"
                )
            )
            return

        # Check if registry has groups when input doesn't
        if len(registry_groups) > 0 and input_group is None:
            # Check if all registry groups are optional
            required_groups = []
            for group_label, group_spec in registry_groups.items():
                is_optional = getattr(group_spec, 'optional', False)
                if not is_optional:
                    required_groups.append(group_label)

            if len(required_groups) > 0:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template registry defines required groups {required_groups} but template input has no group"
                    )
                )
            return

        # Validate the input group if it exists
        if input_group is not None:
            group_parsing_label = input_group.parsing_label if hasattr(input_group, 'parsing_label') else None

            # Check if group exists in registry
            if group_parsing_label not in registry_groups:
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input group '{group_parsing_label}' not found in template registry groups {list(registry_groups.keys())}"
                    )
                )
                return

            # Group validation is complete - just verify the group exists in registry
            # No additional validation needed since GroupSpecs only contains parsing_label

    def _validate_extra_data(self):
        """
        Validate the extra data.
        """
        if (
            not self.template_registry.uses_extra_data
            and len(self.input_extra_data_dict.keys()) > 0
        ):
            self.errors.append(
                InputObjectValidationError(
                    "Template registry does not use extra data but template input has extra data"
                )
            )
        elif self.template_registry.uses_extra_data:
            registry_keys = self.registry_extra_data_dict.keys()
            input_keys = self.input_extra_data_dict.keys()
            if len(input_keys) != len(registry_keys):
                self.errors.append(
                    InputObjectValidationError(
                        f"Template input extra data keys do not match template registry {input_keys} != {registry_keys}"
                    )
                )
            # check for missing keys in the registry
            for key in input_keys:
                if self.registry_extra_data_dict.get(key) is None:
                    self.errors.append(
                        InputObjectValidationError(
                            f"Template input extra data key {key} not in template registry extra data {registry_keys}"
                        )
                    )
            # check for missing keys in the input
            for key in registry_keys:
                if self.input_extra_data_dict.get(key) is None:
                    self.errors.append(
                        InputObjectValidationError(
                            f"Template input extra data key {key} not in template input {input_keys}"
                        )
                    )

    # CANVAS KEY VALIDATION METHODS#
    def _validate_canvas_key(self):
        """
        Validate the canvas key.
        """
        if (
            self.template_input.canvas_key
            not in [preset.id for preset in self.template_registry.canvas_globals.flex_presets.values()]
        ):
            self.errors.append(
                InputObjectValidationError(
                    f"Template input canvas key {self.template_input.canvas_key} not in template registry canvas keys {self.template_registry.canvas_globals.flex_presets.keys()}"
                )
            )
