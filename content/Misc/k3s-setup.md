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
