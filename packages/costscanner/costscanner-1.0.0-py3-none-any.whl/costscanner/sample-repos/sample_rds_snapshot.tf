resource "aws_db_snapshot" "unused_snapshot" {
  db_snapshot_identifier = "snapshot-123"
  db_instance_identifier = "mydb"
}
