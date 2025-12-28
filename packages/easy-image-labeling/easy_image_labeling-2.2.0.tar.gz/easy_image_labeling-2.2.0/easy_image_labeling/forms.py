from typing import Any
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    BooleanField,
    Field,
    FieldList,
    FormField,
    Form,
    MultipleFileField,
    ValidationError,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import InputRequired, Length
from easy_image_labeling.dataset_manager import DatasetManager


class DuplicateDatasetNameValidator:
    """
    Custom validator to ensure that newly added datasets can not have
    the same name as existing ones.
    """

    def __call__(self, form: Form, field: Field) -> Any:
        _input = field.data
        existing_dataset_names = list(
            map(lambda dataset: dataset.address.stem, DatasetManager().managed_datasets)
        )
        if _input in existing_dataset_names:
            raise ValidationError(f"A dataset called {_input} already exists")


class DuplicateStringInputValidator:
    """
    Custom validator to ensure no duplicate values were entered for
    forms that contain field lists.
    """

    def __init__(self, field_name: str) -> None:
        """
        Parameters
        ----------
        field_name: str
            Set name of fields inside field list.
        """
        self.field_name = field_name

    def __call__(self, form: Form, field_list: FieldList) -> Any:
        unique_fields = set()
        raw_fields = list()
        for data_dict in field_list.data:
            unique_fields.add(data_dict[self.field_name])
            raw_fields.append(data_dict[self.field_name])
        if not len(unique_fields) == len(raw_fields):
            raise ValidationError("Fields must not contain duplicate data.")


class NoSpecialCharactersValidator:
    """
    Custom validator to ensure the entered text in the input field does
    not contain any of the specified characters.
    """

    def __init__(self, excluded_characters: list[str] | None = None) -> None:
        """
        Parameters
        ----------
        field_name: str
            Set name of fields inside field list.
        """
        if excluded_characters is None:
            self.excluded_characters = [
                " ",
                "/",
                "\\",
                "*",
                "~",
                "+",
                "&",
                "%",
                "$",
                "§",
                "^",
                "°",
            ]
        else:
            self.excluded_characters = excluded_characters

    def __call__(self, form: Form, field: StringField) -> Any:
        _input = field.data
        if _input is None:
            raise ValidationError("Invalid input.")
        for excluded_character in self.excluded_characters:
            if excluded_character in _input:
                raise ValidationError(
                    f"Input must not contain any '{excluded_character}' characters"
                )


class ForbiddenWordValidator:
    """
    Custom validator to ensure the entered text in the input field is
    not an excluded word.
    """

    def __init__(self, excluded_words: list[str]) -> None:
        """
        Parameters
        ----------
        field_name: str
            Set name of fields inside field list.
        """
        self.excluded_words = excluded_words

    def __call__(self, form: Form, field: StringField) -> Any:
        _input = field.data
        if _input is None:
            raise ValidationError("Invalid input.")
        for excluded_word in self.excluded_words:
            if excluded_word == _input:
                raise ValidationError(f"Label name '{excluded_word}' is not allowed.")


class PictureFolderValidator:
    """
    Checks if selected folder in upload form contains at least one file
    and checks if all files inside folder have supported extensions.
    """

    def __init__(self, allowed_extensions: tuple[str] | None = None) -> None:
        if allowed_extensions is None:
            self.allowed_extensions = ("jpg", "png", "pdf")
        else:
            self.allowed_extensions = allowed_extensions

    def __call__(self, form: Form, field: MultipleFileField) -> Any:
        if not form.files.data:  # type: ignore
            raise ValidationError("No files were selected.")

        for file in form.files.data:  # type: ignore
            if not file.filename:  # Ensures the file has a valid name
                raise ValidationError("Empty file detected.")
            if not (
                "." in file.filename
                and file.filename.rsplit(".", 1)[1] in self.allowed_extensions
            ):
                raise ValidationError(
                    f"Invalid file type: {file.filename}.\nAllowed filetypes are {self.allowed_extensions}"
                )


class MutliButtonForm(FlaskForm):
    label_buttons = FieldList(
        SubmitField("label", render_kw={"class": "button label_button"}),
        "label_buttons",
        min_entries=0,
    )


class LabelNameForm(FlaskForm):
    label_name = StringField(
        "Label",
        validators=[
            InputRequired(),
            Length(min=1, max=20),
            NoSpecialCharactersValidator(),
            ForbiddenWordValidator(["Unknown"]),
        ],
    )


class LabelNameFormContainer(FlaskForm):
    label_names = FieldList(
        FormField(LabelNameForm),
        "All Labels",
        validators=[DuplicateStringInputValidator("label_name")],
        min_entries=0,
    )
    submit = SubmitField()


class UploadDatasetForm(FlaskForm):
    files = MultipleFileField(
        "Upload Files",
        validators=[
            PictureFolderValidator(),
            FileAllowed(
                ["pdf", "jpg", "png"], "Only .png, .pdf or .jpg file types allowed!"
            ),
        ],
    )
    dataset_name = StringField(
        "Dataset name",
        validators=[
            InputRequired(),
            Length(min=1, max=20),
            NoSpecialCharactersValidator(),
            DuplicateDatasetNameValidator(),
        ],
    )
    submit = SubmitField("Upload Files")


class UploadImagesForm(FlaskForm):
    files = MultipleFileField(
        "Upload Files",
        validators=[
            PictureFolderValidator(),
            FileAllowed(
                ["pdf", "jpg", "png"], "Only .png, .pdf or .jpg file types allowed!"
            ),
        ],
    )
    submit = SubmitField("Upload Files")


class RemoveDatasetForm(FlaskForm):
    dataset_name = StringField("dataset_name", render_kw={"readonly": True})
    marked = BooleanField("remove", default=False)


class RemoveMultipleDatasetsForm(FlaskForm):
    remove_datasets_forms = FieldList(
        FormField(RemoveDatasetForm),
        "All Datasets",
        min_entries=0,
    )
    submit = SubmitField()


class EditDatasetForm(FlaskForm):
    dataset_name = StringField("dataset_name", render_kw={"readonly": True})
    add_images_button = SubmitField("Add images")
    remove_images_button = SubmitField("Remove images")


class SelectDatasetToEditForm(FlaskForm):
    edit_dataset_forms = FieldList(
        FormField(EditDatasetForm), "All Datasets", min_entries=0
    )


class ExportLabelsForm(FlaskForm):
    dataset_selection_field = SelectField(
        "Select a dataset",
        choices=[("", "Select a dataset")],
    )
    export_selection_field = SelectField(
        "Export as",
        choices=[("", "Select export ")],
    )
    submit = SubmitField()
