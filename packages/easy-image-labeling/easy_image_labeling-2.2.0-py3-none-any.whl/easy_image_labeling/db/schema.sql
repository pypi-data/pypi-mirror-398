CREATE TABLE
    IF NOT EXISTS Image (
        ImageId INTEGER PRIMARY KEY,
        Dataset TEXT NOT NULL,
        ImageName TEXT NOT NULL,
        DatasetID INTEGER NOT NULL,
        LabelName TEXT NULL,
        LastLabelDate INTEGER NULL,
        UNIQUE (Dataset, DatasetID),
        UNIQUE (Dataset, ImageName),
        UNIQUE (Dataset, ImageName, LastLabelDate),
        FOREIGN KEY (LabelName) REFERENCES Label (LabelName)
    );

CREATE TABLE
    IF NOT EXISTS Label (
        LabelId INTEGER PRIMARY KEY,
        Dataset TEXT NOT NULL,
        LabelName TEXT NOT NULL,
        DatasetID INTEGER NOT NULL,
        UNIQUE (Dataset, LabelName),
        UNIQUE (Dataset, DatasetID)
    );