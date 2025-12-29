resource "aws_db_instance" "unencrypted_rds" {
  identifier         = "mydb"
  instance_class     = "db.t3.micro"
  engine             = "mysql"
  allocated_storage  = 20
  storage_encrypted  = false
}
