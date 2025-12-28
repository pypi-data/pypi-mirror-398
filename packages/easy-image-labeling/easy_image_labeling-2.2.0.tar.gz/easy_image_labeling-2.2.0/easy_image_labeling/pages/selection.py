from easy_image_labeling.forms import (
    LabelNameFormContainer,
    UploadDatasetForm,
    UploadImagesForm,
    RemoveMultipleDatasetsForm,
    SelectDatasetToEditForm,
)
from easy_image_labeling.db.db import (
    sqlite_connection,
    bulk_insert_images,
    get_size_of_dataset,
    remove_dataset_from_db,
    insert_labels,
)
from easy_image_labeling.dataset_manager import Dataset, DatasetManager
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    url_for,
    redirect,
    render_template,
    request,
    session,
)
from pathlib import Path
from werkzeug.utils import secure_filename

bp = Blueprint("config", __name__)


@bp.route("/config/set_number_of_labels", methods=["GET", "POST"])
def configure_labels():
    return render_template("class_number.html")


@bp.route("/config/set_label_names", methods=["POST", "GET"])
def set_number_of_classes():
    if request.method == "POST":
        session["num_classes"] = int(request.form["number_of_classes"])
        label_names_form = LabelNameFormContainer()
        for _ in range(session["num_classes"]):
            label_names_form.label_names.append_entry()
    return render_template("class_names.html", form=label_names_form)


@bp.route("/config/upload_dataset", methods=["POST", "GET"])
def set_class_names():
    upload_form = UploadDatasetForm()
    if request.method == "POST":
        label_names_form = LabelNameFormContainer()
        label_names_form.process(request.form)
        label_names = dict()
        if not label_names_form.validate_on_submit():
            return render_template("class_names.html", form=label_names_form)
        for i, label_name in enumerate(label_names_form.label_names.data):
            label_names[f"label_{i}"] = label_name["label_name"]
        session["label_names"] = label_names
    return render_template(
        "upload_dataset.html", form=upload_form, create_new_dataset=True
    )


@bp.route("/config/upload_folder", methods=["POST"])
def upload_folder():
    if request.method == "POST":
        upload_form = UploadDatasetForm()
        upload_form.process(request.form)
        uploaded_files = request.files.getlist("files")
        dataset_name = upload_form.dataset_name.data
        if dataset_name is None:
            flash("Invalid dataset name.")
            return render_template("index.html")
        dataset_name = secure_filename(dataset_name)
        upload_form.files.data = uploaded_files
        if upload_form.validate_on_submit():
            upload_path = current_app.config["DATASET_FOLDER"] / dataset_name
            if not Path(upload_path).exists():
                Path(upload_path).mkdir(parents=True)  # Ensure upload directory exists
            image_filenames = []
            for file in upload_form.files.data:
                filename = secure_filename(file.filename)
                image_filenames.append(filename)
                file.save(upload_path / filename)
                file.close()
            dataset = Dataset(upload_path)
            DatasetManager().add(dataset)
            with sqlite_connection(current_app.config["DB_URL"]) as cur:
                insert_labels(cur, dataset_name, list(session["label_names"].values()))
                bulk_insert_images(cur, dataset_name, image_filenames, chunk_size=50)
            flash("Files uploaded successfully!", "success")
            return redirect(url_for("index"))
        for field in upload_form.errors:
            if upload_form.errors[field]:
                for error in upload_form.errors[field]:
                    flash(error)
    return redirect(url_for("config.set_class_names"))


@bp.route("/config/remove_datasets", methods=["POST", "GET"])
def select_datasets_to_remove():
    remove_datasets_form = RemoveMultipleDatasetsForm()
    if request.method == "GET":
        for dataset_name in g.dataset_names:
            remove_datasets_form.remove_datasets_forms.append_entry(
                {"dataset_name": dataset_name}
            )
    return render_template("remove_datasets.html", form=remove_datasets_form)


@bp.route("/config/index", methods=["POST"])
def remove_datasets():
    remove_datasets_form = RemoveMultipleDatasetsForm()
    if request.method == "POST":
        remove_datasets_form.process(request.form)
        if remove_datasets_form.validate_on_submit():
            for input_form_data in remove_datasets_form.remove_datasets_forms.data:
                if input_form_data["marked"]:
                    dataset_to_remove = input_form_data["dataset_name"]
                    DatasetManager().remove(dataset_to_remove)
                    with sqlite_connection(current_app.config["DB_URL"]) as cur:
                        remove_dataset_from_db(cur, dataset_to_remove)
                    flash(f"Removed dataset {dataset_to_remove}")
    return redirect(url_for("index"))


@bp.route("/config/select_dataset_to_edit", methods=["GET"])
def select_dataset_to_edit():
    edit_datasets_form = SelectDatasetToEditForm()
    if request.method == "GET":
        for dataset_name in g.dataset_names:
            edit_datasets_form.edit_dataset_forms.append_entry(
                {"dataset_name": dataset_name}
            )
    return render_template("dataset_selection.html", form=edit_datasets_form)


@bp.route("/config/edit_dataset", methods=["GET", "POST"])
def edit_dataset():
    edit_datasets_form = SelectDatasetToEditForm()
    if request.method == "POST":
        edit_datasets_form.process(request.form)
        if edit_datasets_form.validate_on_submit():
            for input_form_data in edit_datasets_form.edit_dataset_forms.data:
                if input_form_data["add_images_button"]:
                    upload_form = UploadImagesForm()
                    return render_template(
                        "upload_dataset.html",
                        form=upload_form,
                        dataset=input_form_data["dataset_name"],
                    )
                if input_form_data["remove_images_button"]:
                    return redirect(
                        url_for(
                            "config.remove_images_from_dataset",
                            dataset=input_form_data["dataset_name"],
                        )
                    )
    return redirect(url_for("config.edit_dataset"))


@bp.route("/config/add_images_to_dataset/<dataset>", methods=["POST"])
def add_images_to_dataset(dataset: str):
    if request.method == "POST":
        upload_form = UploadImagesForm()
        upload_form.process(request.form)
        uploaded_files = request.files.getlist("files")
        upload_form.files.data = uploaded_files
        if upload_form.validate_on_submit():
            upload_path = current_app.config["DATASET_FOLDER"] / dataset
            if not Path(upload_path).exists():
                flash(
                    f"Could not add images to dataset. Dataset {dataset} does not exist.",
                    "error",
                )
                redirect(url_for("index"))
            image_filenames = []
            duplicate_files = []
            for file in upload_form.files.data:
                filename = secure_filename(file.filename)
                if (upload_path / filename).is_file():
                    duplicate_files.append(filename)
                else:
                    image_filenames.append(filename)
                    file.save(upload_path / filename)
                file.close()
            if duplicate_files:
                flash(
                    f"Cannot add files: {", ".join(duplicate_files)} to dataset {dataset}, because it already contains files with the same name.",
                    "info",
                )
            if image_filenames:
                with sqlite_connection(current_app.config["DB_URL"]) as cur:
                    size_of_dataset = get_size_of_dataset(cur, dataset)
                    bulk_insert_images(
                        cur,
                        dataset,
                        image_filenames,
                        chunk_size=50,
                        start_dataset_index=size_of_dataset + 1,
                    )
                flash("Files uploaded successfully!", "success")
            else:
                flash("Failed to upload any files.", "error")
            return redirect(url_for("index"))
        for field in upload_form.errors:
            if upload_form.errors[field]:
                for error in upload_form.errors[field]:
                    flash(error)
    return redirect(url_for("config.select_dataset_to_edit"))


@bp.route("/config/remove_images_from_dataset/<dataset>", methods=["GET"])
def remove_images_from_dataset(dataset: str):
    flash("Feature not implemented yet :(")
    return redirect(url_for("index"))
