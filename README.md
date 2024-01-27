# Origin
Imagine you have a self hosted server at your home and the public ip is changing occasionally. You want to use your own domain to host some services and have your dns setup in aws route53.

# What route53-dyndns does
- fetch public ip of the current machine (where the script is executed)
- set multiple route53 records matching by name to this public ip if it is different
- repeating every 5min.


## docker-compose example:
```
version: '3'

services:
  awsdomain:
  image: tomfankhaenel/route53-dyndns:1.0.0
  restart: always
  environment:
    - ROUTE53_ZONE=$ZONEID
    - ROUTE53_RECORDS=record.,*.record2.
    - AWS_ACCESS_KEY_ID=$KEY
    - AWS_SECRET_ACCESS_KEY=$SECRET
```
