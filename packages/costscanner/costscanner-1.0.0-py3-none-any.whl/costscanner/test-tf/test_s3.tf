resource "aws_s3_bucket" "public_bucket" {
  bucket = "mybucket"
  acl    = "public-read"
}
