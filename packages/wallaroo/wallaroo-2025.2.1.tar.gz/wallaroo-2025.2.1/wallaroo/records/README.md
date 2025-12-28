Python files in this directory are auto generated utilizing [quicktype](https://quicktype.io/#hello).
Introspecting the graphql schema from hasura. You will need a local port-forward to execute the generation.

### GQL 

```
kubectl port-forward -n wallaroo service/graphql-api --address 0.0.0.0 8080
```

```
 npx quicktype \
    --graphql-introspect http://localhost:8080/v1/graphql \
    --http-header "x-hasura-admin-secret: $GRAPHQL_SECRET" \
    --src-lang graphql \
    --lang python api/graphql/convert_keras_model.gql > sdk/wallaroo/records/convert_keras_model.py
```

### JSON

```
npx quicktype --src api/json/telemetry/wallaroo-telemetry-metric-query-v1.json  --src-lang schema --lang python  > sdk/wallaroo/records/v1_metric_response.py
```

### Generate GQL Queries

```
$RepoRoot #>  make gql_to_python
```
