import os
from services.aws_service import read_file_s3
from services.pd_service import (
    get_incident_metadata,
    get_incidents_and_count,
    map_incident_df_to_incident_list_dto,
    read_pd_csv,
    filter_for_casualties,
)
from entity.generated import IncidentFilter, IncidentList, IncidentMetadata
from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

app = Flask(__name__)
load_dotenv()

MAX_PAGE_SIZE = 100

# Configure CORS - restrict to frontend URL in production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
CORS(app, origins=allowed_origins)


def parse_pagination_parameter(
    name: str, default: int, maximum: int | None = None
) -> int:
    """Parse a positive integer query parameter without hiding invalid input."""
    raw_value = request.args.get(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


@app.route("/articles")
def articles() -> Response:
    # fetch df
    df = read_file_s3(os.getenv("S3_ARTICLES_FILENAME"))
    # filter out non relevant articles
    df = df[df["is_relevant"]]
    # sort by date
    df = df.sort_values(by="date_posted", ascending=False)
    # Shape documented by components.schemas.Article in openapi.yaml
    return Response(df.to_json(orient="records"), mimetype="application/json")


@app.route("/incidents")
def incidents() -> tuple[Response, int]:
    # Parse pagination parameters
    try:
        incident_filter: IncidentFilter = IncidentFilter.model_validate_json(
            request.args.get("filter", default="{}")
        )
        page = parse_pagination_parameter("page", default=1)
        page_size = parse_pagination_parameter(
            "pageSize", default=10, maximum=MAX_PAGE_SIZE
        )
    except (ValueError, TypeError) as exc:
        return jsonify(error=str(exc)), 400

    # Fetch paginated incidents
    incidents_df, total = get_incidents_and_count(
        incident_filter.model_dump(exclude_none=True), page=page, page_size=page_size
    )

    # Map to DTO
    mapped_response: IncidentList = map_incident_df_to_incident_list_dto(
        incidents_df, page, page_size, total
    )

    return jsonify(mapped_response.model_dump(mode="json", by_alias=True)), 200


@app.route("/incidents/metadata")
def incident_metadata() -> tuple[Response, int]:
    df = read_pd_csv()
    filtered_df = filter_for_casualties(df)
    metadata: IncidentMetadata = get_incident_metadata(filtered_df)
    return jsonify(metadata.model_dump(mode="json", by_alias=True)), 200
