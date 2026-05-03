# Système de Détection de Menaces basé sur l’Intelligence Artificielle

---

## 1. Introduction

Dans le contexte actuel de la cybersécurité, la détection automatique des menaces est devenue essentielle afin de protéger les systèmes informatiques contre des attaques de plus en plus sophistiquées. Ce projet a pour objectif de concevoir un système de détection de menaces basé sur l’intelligence artificielle, capable de classifier des activités comme étant bénignes ou malveillantes.

Ce travail s’inscrit dans le domaine de la classification supervisée et s’inspire également des concepts utilisés en biométrie, notamment à travers l’utilisation de métriques telles que le FAR (False Acceptance Rate) et le FRR (False Rejection Rate).

---

## 2. Description technique

### 2.1 Architecture du système

Le système développé suit les étapes suivantes :

1. Génération de données  
Un dataset synthétique a été généré afin de simuler des comportements réseau et système.

2. Prétraitement  
Les données sont normalisées avec StandardScaler.

3. Entraînement  
Deux modèles :
- Random Forest
- Régression Logistique

4. Prédiction  
Classification binaire : bénin ou malveillant.

5. Évaluation  
Accuracy, Precision, Recall, F1-score, FAR, FRR, EER.

6. Simulation d’attaques  
Tests de robustesse face à différentes perturbations.

7. Génération des rapports  
Graphiques et fichiers JSON.

---

### 2.2 Algorithmes utilisés

- Random Forest : robuste aux données non linéaires et au bruit  
- Régression Logistique : modèle simple de référence  

- FAR : faux positifs / données bénignes  
- FRR : faux négatifs / données malveillantes  
- EER : point d’égalité entre FAR et FRR  

---

### 2.3 Justification des choix techniques

- Random Forest pour sa robustesse  
- Logistic Regression pour comparaison  
- Dataset synthétique (absence de logs réels)  
- FAR/FRR/EER pertinents en cybersécurité  

---

## 3. Analyse des performances

Résultats en conditions normales :

- Accuracy : 1.00  
- Precision : 1.00  
- Recall : 1.00  
- F1-score : 1.00  
- FAR : 0.00  
- FRR : 0.00  
- EER : 0.00  

Ces résultats montrent une séparation parfaite, mais doivent être relativisés car les données sont synthétiques.

---

## 4. Simulations d’attaques

### 4.1 Attaque par bruit

- Accuracy ~ 0.89  
- FAR ~ 0.15  
- FRR ~ 0.01  

Impact important : augmentation des faux positifs.

---

### 4.2 Attaque de spoofing

- Accuracy ~ 0.99  
- FRR ~ 0.03  

Certaines attaques passent inaperçues.

---

### 4.3 Attaque de compression

Impact faible.

Le modèle reste robuste face à la perte d’information.

---

### 4.4 Attaque adversariale

- Accuracy ~ 0.91  
- FAR ~ 0.12  

Les données proches de la frontière dégradent la performance.

---

## 5. Discussion

Limites :

- Dataset synthétique  
- Pas de données réelles  
- Pas de déploiement réel  

Améliorations :

- Logs réels  
- Deep learning  
- Détection temps réel  
- Robustesse accrue  

---

## 6. Conclusion

Ce projet démontre l’efficacité des méthodes d’apprentissage automatique pour la détection de menaces. Les résultats sont bons en conditions normales mais montrent des limites face aux attaques.

L’analyse FAR, FRR et EER permet une évaluation pertinente dans un contexte de sécurité.
