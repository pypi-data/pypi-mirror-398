from optikka_design_data_layer import logger
from optikka_design_data_layer.db.postgres_client import postgres_client
from optikka_design_data_layer.db.mongodb_guide_client import mongodb_guide_client
from ods_models import WorkflowExecutionResult #pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from psycopg2.extras import RealDictCursor #pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from ods_models import GuideDoc #pylint: disable=relative-beyond-top-level, import-error, no-name-in-module

def get_all_guide_data_by_image(images: list[dict]) -> dict[str, GuideDoc]:
    """
    Get asset data by image.
    """
    image_id_to_guides_map = {}
    for image in images:
        image_id = image.get('image_id', None)
        if image_id is None:
            logger.warning(f"Image ID is required")
            continue
        if (not image.get('type', None)):
            image["type"] = image.get("image_type", None)

        if image.get('type', None) != "LEAF":
            logger.warning(f"Invalid image type for template 2: {image_id}")
            image_id_to_guides_map[image_id] = []
        else:
            workflow_execution_results = []

            with postgres_client.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    # If image is a leaf,
                    # find the originalImageId from the outputImageId via WorkflowExecutionResult table
                    cursor.execute('SELECT * FROM "WorkflowExecutionResult" WHERE "outputImageId" = %s', (image_id,))
                    row = cursor.fetchone()
                    workflow_execution_result = WorkflowExecutionResult(**row) if row else None
                    original_image_id = workflow_execution_result.originalImageId if workflow_execution_result else None

                    # then get all the workflow execution results from the original image
                    workflow_execution_results = postgres_client.get_workflow_execution_results_by_original_image_id(
                        original_image_id
                    )
                    logger.debug(
                        f"Received {len(workflow_execution_results)} workflow execution results: {workflow_execution_results}"
                    )

            # find workflow registry id from workflow batch, and all guides data from wer id
            wer_ids = [workflow_execution_result.id for workflow_execution_result in workflow_execution_results]
            guides = mongodb_guide_client.get_all_guides_by_wer_ids(wer_ids, image_id)
            image_id_to_guides_map[image_id] = guides

    return image_id_to_guides_map


def get_asset_data_by_image_ids(image_ids: list[str]) -> dict:
    """
    Get asset data by image ids.
    """
    assets = []
    assets_final = []
    with postgres_client.get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Use IN clause for multiple IDs
            placeholders = ','.join(['%s'] * len(image_ids))
            cursor.execute(f'SELECT * FROM "Image" WHERE "id" IN ({placeholders})', image_ids)
            rows = cursor.fetchall()
            assets = [dict(row) for row in rows] if rows else []
    for asset in assets:
        logger.debug(f"-----Asset in for loop in get_asset_data_by_image_ids: {asset}")
        asset['image_id'] = asset.get('id')
    logger.debug(f"Assets in get_asset_data_by_image_ids: {assets}")

    image_id_to_guides_map = get_all_guide_data_by_image(assets)
    logger.debug(f"Image id to guides map in get_asset_data_by_image_ids: {image_id_to_guides_map}")
    # Create a dict mapping image_id to asset for easier lookup
    assets_dict = {asset.get('id'): asset for asset in assets}
    for image_id, guides in image_id_to_guides_map.items():
        asset = assets_dict.get(image_id)
        if asset:
            asset['guides'] = guides
            assets_final.append(asset)
    logger.debug(f"Assets final in get_asset_data_by_image_ids: {assets_final}")
    return assets_final
