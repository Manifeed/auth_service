# Review complete de `auth_service/`

Date de revue : 2026-04-29  
Etat revu : implementation courante de `auth_service/`, contrats `shared_backend/`, schema identity dans `infra/postgres_migration/`, integration Docker Compose et cible de test auth-service.

## Synthese executive

`auth_service` est dans un etat nettement plus solide qu'une simple extraction de backend. Le service est court, lisible, stateless cote process, et concentre bien la responsabilite register/login/session/logout derriere des routes internes protegees par token inter-service.

Les bases importantes sont en place :

- Auth inter-services obligatoire en configuration stricte, avec comparaison constant-time.
- Rate limiting login/register par IP et email, adosse a Redis.
- Sessions generees avec forte entropie, stockees en base sous forme de hash.
- Mots de passe hashes via Argon2 dans `shared_backend`.
- Readiness DB reelle via `SELECT 1`.
- Pools DB auth-service dimensionnes plus prudemment pour plusieurs replicas.
- `last_seen_at` amorti au lieu d'etre ecrit a chaque resolution de session.
- Tests unitaires ciblant les protections recemment ajoutees.

Verdict : Avant exposition a du trafic reel ou public, il reste surtout a renforcer la reproductibilite, l'observabilite, les tests d'integration DB, et quelques garanties operationnelles autour de Redis/secrets.

## Ce qui est bien

- Le router reste fin et delegue la logique aux services.
- Les services ne contiennent pas de SQL direct.
- Les requetes SQL sont parametrees avec `sqlalchemy.text()`.
- Les erreurs applicatives passent par les exceptions partagees et les handlers communs.
- Les schemas publics/inter-services viennent de `shared_backend`, ce qui garde un contrat coherent avec `public_api` et les autres services.
- `logout` est idempotent et ne revele pas si le token existait.
- `/internal/health` reste une liveness simple, tandis que `/internal/ready` verifie la configuration critique et la DB.
- Compose force `RATE_LIMIT_REDIS_REQUIRED=true`, `REQUIRE_EXPLICIT_DATABASE_URLS=true` et un healthcheck dedie pour `auth_service`.

## Findings prioritaires

### Eleve - Dependances non reproductibles en production

`auth_service/requirements.txt` depend de `manifeed-shared-backend` via `git+https://github.com/Manifeed/shared_backend.git@main`.

Impact : une image reconstruite demain peut embarquer un contrat different sans changement dans `auth_service`. C'est risqué pour les schemas auth, les erreurs, la politique de mot de passe et les helpers de hash.

Recommandation :

- Pinner `shared_backend` sur un tag semver ou un commit SHA.
- Ajouter un test de contrat minimal entre `auth_service`, `public_api` et `user_service` sur les schemas auth utilises.
- Documenter la procedure de bump de `shared_backend` comme une dependance applicative, pas comme un detail d'image.

### Eleve - Pas encore de test d'integration DB bout en bout

Les tests actuels couvrent la syntaxe, le token interne, le rate limiting et le touch amorti de session. Il manque encore un test qui exerce les tables identity avec un vrai cycle :

`register -> login -> resolve/session -> logout -> resolve invalide`.

Impact : les regressions de mapping SQL, contraintes DB, transactions, timestamps et contrats de reponse peuvent passer jusqu'en staging.

Recommandation :

- Ajouter une suite integration auth-service avec Postgres ephemere ou service Compose dedie.
- Tester les erreurs principales : duplicate registration, invalid credentials, inactive user, expired session, logout idempotent.
- Executer cette suite dans CI avant build d'image.

### Moyen/Eleve - Rate limiting Redis non atomique

Le client Redis fait `INCR`, puis `EXPIRE` si le compteur vaut `1`. Si `INCR` reussit et que `EXPIRE` echoue, la cle peut rester sans TTL.

Impact : un bucket de rate limit peut devenir permanent et bloquer durablement un identifiant. Le risque est rare mais reel lors de coupures reseau ou timeouts partiels.

Recommandation :

- Remplacer `INCR` + `EXPIRE` par un script Lua atomique, ou par une commande equivalente encapsulee dans une librairie Redis robuste.
- Ajouter un test du comportement TTL si un client Redis de test est disponible.

### Moyen - Client Redis maison et connexion par requete

`RedisNetworkingClient` ouvre une socket courte a chaque operation. C'est simple et sans dependance supplementaire, mais les endpoints login/register font deux increments chacun.

Impact : sous charge, le cout reseau Redis peut devenir visible. La gestion des erreurs Redis reste minimale et ne donne pas de metrique exploitable.

Recommandation :

- Evaluer `redis-py` avec pool de connexions si le trafic auth monte.
- Ajouter des logs/metrics pour `rate_limit_allowed`, `rate_limit_blocked` et `rate_limit_redis_unavailable`.
- Conserver le mode fail-closed en production.

### Moyen - Configuration du token interne fragile si `APP_ENV` est mal renseigne

`require_internal_service_token()` autorise le bypass local si `APP_ENV` vaut `dev`, `development`, `local`, `test` ou `testing`. Quand `APP_ENV` est defini, cette valeur prime sur `REQUIRE_INTERNAL_SERVICE_TOKEN`.

Impact : un deploiement mal configure avec `APP_ENV=dev` pourrait bypasser l'auth inter-services, meme si `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.

Recommandation :

- Faire primer explicitement `REQUIRE_INTERNAL_SERVICE_TOKEN=true` sur `APP_ENV`.
- Ajouter un test pour le cas `APP_ENV=dev` + `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.
- En prod/staging, injecter `APP_ENV=production` ou `staging` de facon explicite.

### Moyen - Observabilite encore trop faible

Le service ne produit pas encore de logs structures ni de metrics metier.

Impact : en incident, il sera difficile de distinguer bruteforce, panne Redis, saturation DB, token interne manquant, ou bug applicatif.

Recommandation :

- Ajouter logs structures avec request id/correlation id.
- Ajouter metrics : login success/fail, register success/fail, rate-limit hit, latency service, DB readiness failures, sessions resolved, sessions expired, sessions revoked.
- Surveiller le pool SQLAlchemy et le budget de connexions Postgres.

### Moyen - Hygiene sessions incomplete

Les sessions expirent fonctionnellement a la resolution, mais il n'y a pas de purge periodique des sessions expirees/revoquees, pas de limite de sessions actives par utilisateur, et pas de rotation/renouvellement controle.

Impact : croissance progressive de `user_sessions`, surface d'audit plus bruitée, et controle faible des comptes connectes sur beaucoup d'appareils.

Recommandation :

- Ajouter un job de purge des sessions expirees/revoquees anciennes.
- Ajouter une limite configurable de sessions actives par utilisateur si le produit le demande.
- Documenter la duree de session et la politique de renouvellement.

### Moyen - Image Docker encore perfectible pour la prod

Le Dockerfile utilise `python:3.11-slim`, installe `git`, execute le process en root, et installe la dependance Git au build.

Impact : surface d'image plus large, build dependant du reseau GitHub, et hardening container incomplet.

Recommandation :

- Pinner `shared_backend`, puis installer depuis un package/version ou wheel interne.
- Executer l'application avec un utilisateur non-root.
- Garder `git` hors de l'image runtime si possible via build multi-stage.

### Bas/Moyen - DB client concentre plusieurs responsabilites

`identity_database_client.py` contient records, SQL users, SQL sessions, mapping et normalisation datetime. A la taille actuelle, c'est acceptable et lisible.

Impact : si le domaine identity grossit, ce fichier deviendra un point de concentration et les tests DB seront moins ciblables.

Recommandation :

- Decouper plus tard en `identity_user_database_client.py`, `identity_session_database_client.py` et `records.py` si le fichier continue a grossir.
- Ajouter tests de mapping SQL avant refactor.

## Securite detaillee

### Mots de passe

Bon :

- Argon2 via `shared_backend.utils.auth_utils`.
- Politique minimale : 12 caracteres, liste courte de mots de passe communs, diversite minimale.
- Login retourne une erreur generique pour email inconnu ou mot de passe incorrect.

Reste a faire :

- Detection de mots de passe compromis.
- Rehash automatique si les parametres Argon2 changent.
- Tests unitaires dedies au register/login avec politique de mot de passe.

### Sessions

Bon :

- Token aleatoire de 32 bytes avec prefixe clair.
- Stockage uniquement du hash SHA-256 du token.
- Resolution refuse token manquant, invalide, expire ou utilisateur inactif.
- `last_seen_at` amorti par `AUTH_SESSION_TOUCH_INTERVAL_SECONDS`, defaut 300 secondes.

Reste a faire :

- Purge des sessions expirees/revoquees.
- Limite de sessions actives.
- Eventuel HMAC/pepper serveur pour le hash de token si l'on veut reduire encore l'impact analytique d'une fuite DB.

### Inter-service

Bon :

- Header dedie `x-manifeed-internal-token`.
- Secret requis hors environnements locaux.
- Longueur minimale de 32 caracteres hors local.
- Comparaison avec `secrets.compare_digest`.
- Compose injecte `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.

Reste a faire :

- Faire primer `REQUIRE_INTERNAL_SERVICE_TOKEN=true` sur `APP_ENV`.
- Remplacer a terme le secret global par mTLS ou JWT inter-service court avec audience/scopes.
- Mutualiser l'implementation dans `shared_backend` pour eviter les divergences entre services.

### Rate limiting

Bon :

- Login limite par IP et email.
- Register limite par IP et email.
- Redis obligatoire dans Compose pour auth-service.
- Fallback memoire disponible pour local/dev si Redis n'est pas requis.

Reste a faire :

- Atomicite TTL Redis.
- Backoff progressif sur erreurs credentials.
- Metrics et alerting.

## Architecture

Le decoupage est coherent pour un service FastAPI interne :

- `app/routers` : expose les contrats HTTP internes.
- `app/services` : porte les cas d'usage auth.
- `app/clients/database` : isole SQLAlchemy et SQL brut.
- `app/clients/networking` : isole Redis.
- `app/middleware` : contient le rate limiting applicatif.
- `shared_backend/security/internal_service_auth.py` : gere l'auth inter-services.
- `shared_backend` : source des schemas, erreurs et helpers transverses.

Le service ne parait pas sur-architecturé. Les imports d'erreurs et de securite pointent maintenant directement vers `shared_backend`, ce qui reduit la duplication locale.

## Scalabilite horizontale

Ce qui scale correctement :

- Process stateless.
- Sessions en Postgres partagees entre replicas.
- Rate limit centralise dans Redis en configuration Compose.
- Pool DB par replica plus raisonnable : `5 + 10 overflow` par defaut.
- `last_seen_at` n'est plus mis a jour a chaque requete authentifiee.

Points a surveiller :

- Chaque login/register fait deux appels Redis.
- Chaque resolution de session lit Postgres.
- Pas encore de cache court TTL pour session.
- Le budget de connexions Postgres doit rester explicite : `replicas * (pool_size + max_overflow) <= budget_auth`.

## Contrats API actuels

Routes internes :

- `GET /internal/health` : liveness statique.
- `GET /internal/ready` : readiness config + DB.
- `POST /internal/auth/register` : cree un utilisateur actif role `user`.
- `POST /internal/auth/login` : cree une session et retourne le token clair.
- `POST /internal/auth/session` : retourne l'utilisateur courant et expiration.
- `POST /internal/auth/resolve-session` : retourne le contexte minimal inter-service.
- `POST /internal/auth/logout` : revoque de facon idempotente.

Comportements a documenter explicitement :

- `logout` retourne `ok=True` meme pour token inconnu.
- Les erreurs duplicate registration peuvent reveler qu'un email ou pseudo existe deja.
- La readiness peut echouer si le token interne est absent en mode strict, meme si la DB est disponible.

## Tests et verification

Tests presents :

- Syntaxe de tous les fichiers Python du service.
- Token interne absent autorise en local.
- Token interne absent refuse en production.
- Token interne valide accepte en production.
- Redis requis et indisponible bloque le rate limiting.
- Fallback memoire quand Redis est optionnel.
- Resolution de session sans touch si `last_seen_at` est recent.
- Resolution de session avec touch si `last_seen_at` est stale.

Verifications executees pendant cette revue :

- `python3 -m compileall -q auth_service` : OK.
- `docker compose -f docker-compose.yml config --quiet` depuis `infra/` : OK.
- `make test-auth-service` depuis `infra/` : OK, 8 tests passes.

Limites de verification :

- Pas de test d'integration avec Postgres reel.
- Pas de test Redis reel.
- Pas de test de demarrage complet Compose avec tous les services.

## Plan d'action recommande

### P0 - Avant prod exposee

- Pinner `shared_backend` sur tag ou commit SHA.
- Ajouter test integration DB register/login/resolve/logout.
- Rendre le rate limit Redis atomique.
- Faire primer `REQUIRE_INTERNAL_SERVICE_TOKEN=true` sur `APP_ENV`.
- Ajouter logs structures minimaux et compteurs rate-limit/login.

### P1 - Stabilisation

- Ajouter purge sessions expirees/revoquees.
- Ajouter metrics DB pool et readiness failures.
- Durcir l'image Docker avec utilisateur non-root et build plus reproductible.
- Ajouter tests sur register/login/logout et erreurs metier.

### P2 - Long terme

- Mutualiser la securite inter-service dans `shared_backend`.
- Introduire identite/scopes inter-services au lieu d'un token global.
- Evaluer cache session court TTL avec invalidation prudente.
- Decouper le client DB si le domaine identity grossit.
