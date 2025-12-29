resource "aws_ebs_volume" "unattached_volume" {
  availability_zone = "us-east-1a"
  size              = 20
}
