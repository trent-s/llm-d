# Well-lit Path: WEKA GPU Direct

Full doc coming soon, this is just meant to track the changes in this PR for now.

1. Add a readiness prob script to the `llm-d` image to detect if the cufile exists on the node and is properly formatted
2. InitContainer added to run `amgctl` to create the cufile on the node (only implemented for decode so far, will need to add this for prefill too)
3. Mount the cufile.json from ~/amg_stable/cufile.json on the host to ~/amg_stable/cufile.json on the container

## Usage

```bash
helm install llama-33-70B-Instruct-FP8-dynamic \
    -n ${NAMESPACE} \
    -f inferencepool.values.yaml \
    oci://us-central1-docker.pkg.dev/k8s-staging-images/gateway-api-inference-extension/charts/inferencepool --version v0.5.1
```
