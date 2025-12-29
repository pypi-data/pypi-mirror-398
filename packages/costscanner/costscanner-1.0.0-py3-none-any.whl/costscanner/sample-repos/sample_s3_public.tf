resource "aws_s3_bucket" "public_bucket" {
  bucket = "public-bucket"
  acl    = "public-read"
}
