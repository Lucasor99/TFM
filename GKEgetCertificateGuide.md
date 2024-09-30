# Steps to install nginx ingress controller on GKE and get a certificate https

```bash
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole cluster-admin \
  --user $(gcloud config get-value account)
```

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/cloud/deploy.yaml
```

```bash
kubectl get svc --namespace=ingress-nginx
```

```bash
//kubectl apply -f DeployFiles/web-ingress.yaml
```

 ```bash
 kubectl  create namespace cert-manager
```
```bash
  kubectl   apply   -f   https://github.com/cert-manager/cert-manager/releases/download/v1.15.2/cert-manager.yaml
```

Modify the domain name in the file `prod_issuer.yaml` and run the following command:

```bash
   kubectl    create    -f    DeployyFiles/prod_issuer.yaml
```