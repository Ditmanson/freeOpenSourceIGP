---
date: '2026-07-04'
title: 'K3s Setup'
---

# Pre-reqs
1. Install OS on machines, [Debian iso's](https://debian.osuosl.org/debian-cdimage/13.5.0/)
2. We need to configure static ip's for these machines and for [metallb](https://metallb.io/)
3. SSH access

I gave you debian as an example because most instructions are written for ubuntu, and ubuntu is based on debian, just with extra garbage preinstalled. If it turns out we need any of that we'll get it when we need it. A lot of people, probably including your ai, are going
to recommend [Talos](https://www.siderolabs.com/talos-linux), Because it's written for kubernetes. But there's less examples of using it on the internet. So more security but harder to work with. **Do not use anything Arch based**, it's funner but it breaks alot and I don't think it's going to be a good fit for you. 

When you do the install on these machines. We probably want a desktop for 1 machine. That machine will be our server node, and we can use it to control your cluster, run your database, look at metrics and all that. Any additional machines we use for the cluster can be headless to save on resources. If that doesn't make sense, then just ask your ai while you do this.

When you run this through your AI, couple things to add to your prompt. You are going to want to verify the hash on the iso, ask your ai how to do that. Pretty common vulnerability in linux is downloading OS's with additional stuff in them. We verify the sha256 hash to ensure we aren't grabbing extra stuff _like virus's or spyware_ 

When you run the ssh commands, you'll get a public key and a private key. If your private key makes it on the internet in any way, then we want to delete it, make a new pair, and then replace public keys anywhere we might have put them.

Do not give the private key to claude or your buddy. If you want to set remote access to the system, then we can do that later with [tailscale](https://tailscale.com/)

Also if you want me to do all this with/for you then we can do that too. Just not gonna give you copy and paste commands because I have all this set up already.

{{< youtube 7gkVUIlzOzg >}}

- Commands for ssh `ssh-keygen` just take defaults.
- copy the public key from your host machine to your remote `ssh <username>@<local ip>` first time you need a password
- paste the public key at `~/.ssh/authoized_keys`
{{< youtube  HbCYeQNs0E4  >}}

# K3s install
## Server node
- `curl -sfL https://get.k3s.io | sh -s - server   --write-kubeconfig-mode 644   --disable servicelb` <- for the control/server node
- `sudo cat /etc/rancher/k3s/k3s.yaml > ~/.kube/kubeconfig` <- for putting the kubeconfig in the defualt location
- `sudo cat /var/lib/rancher/k3s/server/node-token` <- for grabbing the token to add worker nodes
## Worker node
- `curl -sfL https://get.k3s.io | K3S_URL=https://<ENTER YOUR SERVER IP>:6443 K3S_TOKEN=<ENTER YOUR NODE-TOKEN>  sh -s -`

## Test from server node
- `kubectl get nodes`
- [download kubectl if you don't have it](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)

{{< youtube muxITGejyjI >}}

# Metallb
{{< youtube xZiR43fAalQ >}}
- `kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.16.1/config/manifests/metallb-native.yaml` <- install loadbalancers
- `kubectl get pods -A` <- ensure you can see the loadbalancers
- create an ipaddresspool.yaml
```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: adress-pool
  namespace: metallb-system
spec:
  addresses:
  - <change to your cidr range>
```
- `kubectl apply -f ipaddresspool.yaml` <- set the cidr range for your loadbalancers
- creat l2config.yaml
```yaml
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: adress-pool
  namespace: metallb-system
```
- `kubectl apply -f l2config.yaml` <- apply l2config
## Testing it
- mkdir test
- cd test
- create deploy.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx
spec:
  selector:
    matchLabels:
      run: my-nginx
  replicas: 2
  template:
    metadata:
      labels:
        run: my-nginx
    spec:
      containers:
      - name: my-nginx
        image: nginx
        ports:
        - containerPort: 80
```
- `kubectl apply -f deploy.yaml` <- apply deployment
- create service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nginx
  labels:
    run: my-nginx
spec:
  type: LoadBalancer
  ports:
  - port: 80
    protocol: TCP
  selector:
    run: my-nginx
```

- `kubectl apply -f service.yaml` <- apply service
- `kubectl get svc` <- check if you have a service and that it's running on an ip
- `kubectl get pods -w` <- wait for pods to come up, ctrl+c to exit this watch screen
## Clean up test
- `kubectl delete -f deploy.yaml`
- `kubectl delete -f service.yaml`

# A note about my notes
I'm running into some issues with my OS of choice here. I'm going to switch over to debian, this will mean i won't have screen recording until I get around to setting it up.

# istio
I didn't take real good notes for this. We want istio for our ingress/egress in and out of our deployed applications. Later we'll make k8 resources for it but for now I ran these commands:

```bash

curl -L https://istio.io/downloadIstio | sh -
sudo mv bin/istioctl /usr/bin/
istioctl
istioctl install --set profile=default -y
```
- [docs for istio install](https://istio.io/latest/docs/setup/install/istioctl/)

After it all installs let's make sure we have all the correct resources. I'm gonna paste my output below:

```bash
# kubectl get svc -A

NAMESPACE        NAME                          TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)                                      AGE
default          kubernetes                    ClusterIP      10.43.0.1       <none>          443/TCP                                      4h41m
istio-system     istio-ingressgateway          LoadBalancer   10.43.92.106    192.168.1.201   15021:30629/TCP,80:32725/TCP,443:30697/TCP   4h8m
istio-system     istiod                        ClusterIP      10.43.6.143     <none>          15010/TCP,15012/TCP,443/TCP,15014/TCP        4h9m
istio-system     istiod-revision-tag-default   ClusterIP      10.43.56.157    <none>          15010/TCP,15012/TCP,443/TCP,15014/TCP        4h8m
kube-system      kube-dns                      ClusterIP      10.43.0.10      <none>          53/UDP,53/TCP,9153/TCP                       4h41m
kube-system      metrics-server                ClusterIP      10.43.120.98    <none>          443/TCP                                      4h41m
kube-system      traefik                       LoadBalancer   10.43.3.87      192.168.1.200   80:30685/TCP,443:31688/TCP                   4h39m
metallb-system   metallb-webhook-service       ClusterIP      10.43.195.185   <none>          443/TCP                                      4h19m
```
Up there there in the services, the one we are looking for has the type Load Balancer, it's in the istio-system namespace and it's name isistio-ingressgateway. You see the External-IP there, that's where we redirect our router network to go and we'll just use port 443:80. 

```bash
# kubectl get pods -A

NAMESPACE        NAME                                      READY   STATUS      RESTARTS        AGE
istio-system     istio-ingressgateway-5fdd5ff474-8s7pc     1/1     Running     0               38m
istio-system     istiod-5688cf5cb9-9c6tf                   1/1     Running     1 (38m ago)     4h10m
kube-system      coredns-5f5694d56b-vzvws                  1/1     Running     1 (38m ago)     4h42m
kube-system      csi-nfs-controller-fccdc96d7-gc7qc        5/5     Running     9 (23m ago)     4h6m
kube-system      csi-nfs-node-xhs8x                        3/3     Running     3 (38m ago)     4h6m
kube-system      csi-nfs-node-xncrf                        3/3     Running     3 (38m ago)     4h6m
kube-system      helm-install-traefik-crd-fcrgg            0/1     Completed   0               4h42m
kube-system      helm-install-traefik-w9vdg                0/1     Completed   1 (4h41m ago)   4h42m
kube-system      local-path-provisioner-58d557dc48-xm6zk   1/1     Running     1 (38m ago)     4h42m
kube-system      metrics-server-7c86f97b8d-fsgxk           1/1     Running     1 (38m ago)     4h42m
kube-system      traefik-6cd8c7cd89-mz7zb                  1/1     Running     1 (38m ago)     4h41m
metallb-system   controller-658745d67-mjq6r                1/1     Running     1 (38m ago)     4h20m
metallb-system   speaker-tlllg                             1/1     Running     1 (38m ago)     4h20m
metallb-system   speaker-xgt7m                             1/1     Running     1 (38m ago)     4h20m
```
# NFS csi server
I also didn't take good notes for setting up the NFS server, but it's probably going to be way different for you anyways.
- [Helm Charts](https://github.com/kubernetes-csi/csi-driver-nfs), we'll use these to install it but not yet, first we need to prep the nas.
- [NFS Setup](https://canonical.com/microk8s/docs/how-to-nfs) <- this has instructions for tting up our file sharing system on a linux distro. Your NAS you bought is probably going to be different. The steps for some of this will be the same though:
1. We need to make a partition or share with open permissions available to everyone, or atleast the users we designate.
2. We need to expose that share/partition to a cidr range with some permission sets.
3. Then we need to install the K8 resources with helm.
4. And finally we build a storage class object for it.
5. Test it
## Helm
```bash
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system --version 4.12.0
```
For the storga Class object, it's gonna be better we just provide your AI with the information about the share/partition you made and let it give make it, on that note we'll have your ai make a pvc resource to test it as well. 

# Database
This might end up being the hard part for you. I'm going to deploy a database on the cluster. We might consider hosting this differently on your setup if anything goes wrong here. This is a part where we'd start setting stuff up for your application as well. I'm not deploying my own app right now, so I'm going to be deploying a photo server instead. So this is an example, not a step by step copy and paste this time.

## Helm install of cnpg
From [helm docs](https://github.com/cloudnative-pg/charts/tree/main/charts/cloudnative-pg)
```bash
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update
```

```bash
helm upgrade --install cnpg \
  --namespace cnpg-system \
  --create-namespace \
  cnpg/cloudnative-pg
```
