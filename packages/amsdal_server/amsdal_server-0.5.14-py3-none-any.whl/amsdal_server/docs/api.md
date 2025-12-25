The API server is a RESTful API that allows you to perform CRUD operations on the data stored in the database.
The API server is built using the FastAPI framework.

You can use AMSDAL CLI to run the development API server locally with amsdal serve command.

## Authentication

By default, AMSDAL Server does not require authentication for API requests. You can enable authentication by setting
permissions for your models. 

See more details about Auth mechanism of AMSDAL Auth plugin here: 
[AMSDAL Auth](https://docs.amsdal.com/server/amsdal-auth/)

In order to authorize you need to get token and put it into `Authorization` header.

Use the [/api/objects/](https://docs.amsdal.com/server/api/server-api/#post-apiobjects) to get token by user's
email and password. For example, using cURL:

```bash
curl --location 'https://example.com/api/objects/?class_name=LoginSession' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "myuser@example.com",
    "password": "myuserpassword"
}'
```

!!! note
    Replace `example.com` domain to yours one.

After receiving token, you need to put it in `Authorization` header. For example:

```
Authorization: hSdjw1723bbdfFLqwJgah32
```

## Filters

Some endpoints support filtering. You can filter the results by adding a query parameter `filter` to the URL.

To use filters, use the following syntax:

```
?filter[<field_name>__<field_type>]=<value>
```

where - `field_name` - the name of the field you want to filter by - `field_type` - filter operator

We support the following filter types:

- eq - equal
- neq - not equal
- gt - greater than to value
- gte - greater than or equal to value
- lt - less than to value
- lte - less than or equal to value
- contains - contains the value (case sensitive)
- startswith - starts with value (case sensitive)

Examples:

```
/classes/Person?filter[firstname__eq]=Employee
```

```
/classes/Person?filter[firstname__startswith]=Empl
```

## Fields restrictions

In order to optimize requests, we want to omit some fields when querying for objects.

To do this, we should be able to [optionally specify](https://jsonapi.org/format/#fetching-sparse-fieldsets)
a `fields[TYPE]` field in the object request that will accept, separated by commas, the fields we want to receive from
the server. TYPE - is the type of requested object, so in the common case it will be name of the requested class,
or `Metadata`.

For example:

```
/classes/EmployeeProfile?include_metadata=true&fields[EmployeeProfile]=first_name,last_name&fields[Metadata]=address,version_id
```

All object fields with some metadata fields:

```
/classes/EmployeeProfile?fields[Metadata]=lakehouse_address
```

You can limit to only one field:

```
/classes/EmployeeProfile?fields[Metadata]=lakehouse_address&fields[EmployeeProfile]=first_name
```

Also, you can omit all the fields, just leave the values blank:

```
/classes/EmployeeProfile?fields[Metadata]=lakehouse_address&fields[EmployeeProfile]=
```
