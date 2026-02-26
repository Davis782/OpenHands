CREATE TABLE IF NOT EXISTS group_members (
    group_id TEXT NOT NULL,
    pearl_id TEXT NOT NULL,
    PRIMARY KEY (group_id, pearl_id),
    FOREIGN KEY (group_id) REFERENCES pearl_id_groups(group_id) ON DELETE CASCADE
);