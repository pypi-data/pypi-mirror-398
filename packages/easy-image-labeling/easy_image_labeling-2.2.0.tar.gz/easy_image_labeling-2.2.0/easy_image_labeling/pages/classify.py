from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    current_app,
    request,
    g,
    session,
    flash,
)
from easy_image_labeling.db.db import (
    sqlite_connection,
    get_lowest_dataset_id,
    get_next_dataset_id,
    get_previous_dataset_id,
    get_labels,
    get_skipped_image_ids,
    get_size_of_dataset,
    get_image_name,
    get_num_of_labelled_images,
    set_image_label,
    reset_dataset_labels,
)
from easy_image_labeling.forms import MutliButtonForm

bp = Blueprint("classify", __name__)


def create_multibutton_form(labels: list[str]) -> MutliButtonForm:
    multi_button_form = MutliButtonForm()
    for i, label in enumerate(labels):
        multi_button_form.label_buttons.append_entry(label)
        multi_button_form.label_buttons[i].label.text = label
        multi_button_form.label_buttons[i].id = label
    return multi_button_form


@bp.route("/classify/<dataset>", methods=["POST", "GET"])
def classify_next_image(dataset: str):
    """
    Retrieve the lowest image id of all unlabelled images in the
    specified dataset (skipped images do not count as unlabelled)
    and redirect the user to the clasification page of the image
    with this image id. If all images in the dataset are labelled,
    redirect user to classification summary page.
    """
    only_skipped = request.args.get("only_skipped", "False").lower() == "true"
    with sqlite_connection(current_app.config["DB_URL"]) as cur:
        dataset_id = get_lowest_dataset_id(cur, dataset, only_skipped)
    if dataset_id is None:
        session["allowed_to_view_summary"] = True
        return redirect(url_for("classify.classification_summary", dataset=dataset))

    return redirect(
        url_for(
            "classify.classify",
            dataset=dataset,
            id=dataset_id,
            only_skipped=only_skipped,
        )
    )


@bp.route("/classify/<dataset>/summary", methods=["GET"])
def classification_summary(dataset: str):
    """
    Display a small summary for the specified dataset. This URL
    endpoint can not be accessed manually.
    """
    if not session.pop("allowed_to_view_summary", False):  # Check and remove flag
        flash(
            f"The summary screen can only be accessed once all images of the dataset {dataset} have been labelled or skipped."
        )
        flash("Manually accessing this page is forbidden.")
        return redirect(url_for("index"))
    with sqlite_connection(current_app.config["DB_URL"]) as cur:
        skipped_image_ids = get_skipped_image_ids(cur, dataset)
        g.num_skipped_images = len(skipped_image_ids)
        # Number of labelled images = Number of all images - Number of skipped images,
        # only works if there are no unlabelled images in the dataset
        g.num_labelled_images = get_size_of_dataset(cur, dataset) - g.num_skipped_images
    return render_template(
        "classification_summary.html", dataset=dataset, only_skipped=True
    )


@bp.route("/classify/<dataset>/<id>", methods=["POST", "GET"])
def classify(dataset: str, id: int):
    """
    Render html template for displaying one image from given Dataset
    and DatasetID and form for labelling said image.
    """
    only_skipped = request.args.get("only_skipped", "False").lower() == "true"
    with sqlite_connection(current_app.config["DB_URL"]) as cur:
        dataset_labels = get_labels(cur, dataset)
        num_labelled_images = get_num_of_labelled_images(cur, dataset)
        total_num_images = get_size_of_dataset(cur, dataset)
        image_name = get_image_name(cur, dataset, id)
    image_address = f"datasets/{dataset}/{image_name}"
    multi_button_form = create_multibutton_form(dataset_labels)
    return render_template(
        "classify_image.html",
        image=image_address,
        form=multi_button_form,
        dataset=dataset,
        image_id=id,
        num_labelled=num_labelled_images,
        num_total=total_num_images,
        only_skipped=only_skipped,
    )


@bp.route("/classify/<dataset>/<id>/submit", methods=["POST"])
def submit_classification(dataset: str, id: int):
    """
    Process the submitted form, update image label in the database, and
    load the next image.
    """
    only_skipped = request.args.get("only_skipped", "False").lower() == "true"
    multi_button_form = MutliButtonForm()
    id = int(id)
    if request.method == "POST":
        if multi_button_form.validate_on_submit():
            for k, v in request.form.items():
                if k.startswith("label_buttons"):
                    selected_label = v

        with sqlite_connection(current_app.config["DB_URL"]) as cur:
            set_image_label(cur, dataset, id, selected_label)
            next_id = get_next_dataset_id(cur, dataset, id, only_skipped)
            if next_id is None:
                return redirect(
                    url_for(
                        "classify.classify_next_image",
                        dataset=dataset,
                        only_skipped=only_skipped,
                    )
                )

    return redirect(
        url_for(
            "classify.classify", dataset=dataset, id=next_id, only_skipped=only_skipped
        )
    )


@bp.route("/classify/<dataset>/reset", methods=["POST"])
def reset_all_labels(dataset: str):
    with sqlite_connection(current_app.config["DB_URL"]) as cur:
        reset_dataset_labels(cur, dataset)
    return redirect(url_for("classify.classify_next_image", dataset=dataset))


@bp.route("/classify/<dataset>/<id>/skip", methods=["POST"])
def handle_move_button(dataset: str, id: int):
    """
    Process the submitted form, update image label in the database, and
    load the next image.
    """
    only_skipped = request.args.get("only_skipped", "False").lower() == "true"
    action = request.form.get("action")
    id = int(id)
    match action:
        case "skip":
            with sqlite_connection(current_app.config["DB_URL"]) as cur:
                set_image_label(cur, dataset, id, None)
                next_id = get_next_dataset_id(cur, dataset, id, only_skipped)
            if next_id is None:
                return redirect(
                    url_for(
                        "classify.classify_next_image",
                        dataset=dataset,
                        only_skipped=only_skipped,
                    )
                )
            return redirect(
                url_for(
                    "classify.classify",
                    dataset=dataset,
                    id=next_id,
                    only_skipped=only_skipped,
                )
            )
        case "back":
            with sqlite_connection(current_app.config["DB_URL"]) as cur:
                previous_id = get_previous_dataset_id(cur, dataset, id, only_skipped)
            if previous_id is None:
                return redirect(
                    url_for(
                        "classify.classify",
                        dataset=dataset,
                        id=id,
                        only_skipped=only_skipped,
                    )
                )
            return redirect(
                url_for(
                    "classify.classify",
                    dataset=dataset,
                    id=previous_id,
                    only_skipped=only_skipped,
                )
            )
        case _:
            flash("An unknown error occured.")
            return redirect(url_for("/"))
