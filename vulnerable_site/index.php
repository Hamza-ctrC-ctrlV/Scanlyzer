<?php require_once 'form_handler.php'; ?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AtlasBank – Ouvrir un Compte</title>
    <link rel="stylesheet" href="style.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
</head>
<body>

<!-- ========== HEADER ========== -->
<header class="header" id="top">
    <div class="header-inner container">
        <a href="#top" class="logo">
            <span class="logo-icon">⬡</span>
            <span class="logo-text">Atlas<strong>Bank</strong></span>
        </a>
        <nav class="nav">
            <a href="#top" class="nav-link active">Accueil</a>
            <a href="#comptes" class="nav-link">Comptes</a>
            <a href="#services" class="nav-link">Services</a>
            <a href="#contact" class="nav-link">Contact</a>
        </nav>
        <a href="#formulaire" class="btn-header">Ouvrir un compte</a>
        <button class="burger" id="burger" aria-label="Menu">
            <span></span><span></span><span></span>
        </button>
    </div>
    <div class="mobile-nav" id="mobileNav">
        <a href="#top" class="nav-link">Accueil</a>
        <a href="#comptes" class="nav-link">Comptes</a>
        <a href="#services" class="nav-link">Services</a>
        <a href="#contact" class="nav-link">Contact</a>
    </div>
</header>

<!-- ========== HERO ========== -->
<section class="hero">
    <div class="hero-bg"></div>
    <div class="container hero-content">
        <p class="hero-eyebrow">Banque Personnelle & Professionnelle</p>
        <h1 class="hero-title">Votre avenir financier<br><em>commence ici.</em></h1>
        <p class="hero-desc">AtlasBank vous accompagne à chaque étape de votre vie avec des solutions bancaires personnalisées, sécurisées et accessibles partout au Maroc.</p>
        <div class="hero-actions">
            <a href="#formulaire" class="btn btn-primary">Ouvrir un compte</a>
            <a href="#services" class="btn btn-ghost">Découvrir nos services</a>
        </div>
        <div class="hero-stats">
            <div class="stat"><strong>2.4M+</strong><span>Clients</span></div>
            <div class="stat-sep"></div>
            <div class="stat"><strong>320+</strong><span>Agences</span></div>
            <div class="stat-sep"></div>
            <div class="stat"><strong>30 ans</strong><span>d'expertise</span></div>
        </div>
    </div>
    <div class="hero-image-side">
        <div class="card-float card-1">
            <span class="card-label">Compte Épargne</span>
            <span class="card-num">•••• •••• •••• 4821</span>
            <span class="card-rate">Taux : <b>3.5%</b></span>
        </div>
        <div class="card-float card-2">
            <span class="card-label">Solde disponible</span>
            <span class="card-amount">24 850,00 MAD</span>
        </div>
    </div>
</section>

<!-- ========== COMPTES ========== -->
<section class="section" id="comptes">
    <div class="container">
        <div class="section-header">
            <p class="section-eyebrow">Nos produits</p>
            <h2 class="section-title">Des comptes pour chaque profil</h2>
        </div>
        <div class="cards-grid">
            <div class="offer-card">
                <div class="offer-icon">⬡</div>
                <h3>Compte Courant</h3>
                <p>Gérez vos opérations quotidiennes avec une carte bancaire internationale et un accès digital 24h/7j.</p>
                <ul>
                    <li>Carte Visa Gold incluse</li>
                    <li>Virements illimités</li>
                    <li>Application mobile avancée</li>
                </ul>
                <a href="#formulaire" class="btn btn-outline">Souscrire</a>
            </div>
            <div class="offer-card featured">
                <div class="offer-badge">Recommandé</div>
                <div class="offer-icon">◈</div>
                <h3>Compte Épargne</h3>
                <p>Faites fructifier votre épargne avec un taux préférentiel et des conditions avantageuses.</p>
                <ul>
                    <li>Taux jusqu'à 3.5%</li>
                    <li>Retraits flexibles</li>
                    <li>Tableau de bord épargne</li>
                </ul>
                <a href="#formulaire" class="btn btn-primary">Souscrire</a>
            </div>
            <div class="offer-card">
                <div class="offer-icon">◇</div>
                <h3>Compte Professionnel</h3>
                <p>Une solution complète pour les entrepreneurs, TPE et PME avec des services dédiés aux entreprises.</p>
                <ul>
                    <li>Domiciliation d'entreprise</li>
                    <li>Lignes de crédit pro</li>
                    <li>Conseiller dédié</li>
                </ul>
                <a href="#formulaire" class="btn btn-outline">Souscrire</a>
            </div>
        </div>
    </div>
</section>

<!-- ========== SERVICES ========== -->
<section class="section section-alt" id="services">
    <div class="container">
        <div class="section-header">
            <p class="section-eyebrow">Ce que nous offrons</p>
            <h2 class="section-title">Des services pensés pour vous</h2>
        </div>
        <div class="services-grid">
            <div class="service-item">
                <span class="service-icon">🔒</span>
                <h4>Sécurité renforcée</h4>
                <p>Authentification biométrique et surveillance anti-fraude en temps réel.</p>
            </div>
            <div class="service-item">
                <span class="service-icon">📱</span>
                <h4>Banque mobile</h4>
                <p>Gérez vos finances depuis votre smartphone, n'importe où, n'importe quand.</p>
            </div>
            <div class="service-item">
                <span class="service-icon">💳</span>
                <h4>Cartes premiums</h4>
                <p>Visa Gold, Platinum et Business avec avantages exclusifs et assurances voyages.</p>
            </div>
            <div class="service-item">
                <span class="service-icon">🏠</span>
                <h4>Crédit immobilier</h4>
                <p>Réalisez votre projet de logement avec des taux compétitifs et un accompagnement personnalisé.</p>
            </div>
            <div class="service-item">
                <span class="service-icon">📈</span>
                <h4>Investissement</h4>
                <p>Portefeuille boursier, OPCVM et assurance-vie pour faire croître votre patrimoine.</p>
            </div>
            <div class="service-item">
                <span class="service-icon">🌍</span>
                <h4>Transferts internationaux</h4>
                <p>Envoyez et recevez des fonds dans plus de 150 pays avec des frais réduits.</p>
            </div>
        </div>
    </div>
</section>

<!-- ========== FORMULAIRE ========== -->
<section class="section" id="formulaire">
    <div class="container">
        <div class="section-header">
            <p class="section-eyebrow">Rejoignez-nous</p>
            <h2 class="section-title">Ouvrir un compte en ligne</h2>
            <p class="section-sub">Complétez ce formulaire et un conseiller vous contactera sous 24 heures ouvrées.</p>
        </div>

        <?php if (!empty($success_message)): 
            /** @var array $submitted_data */?>
        <!-- CONFIRMATION — affiche les données brutes (intentionnellement vulnérable) -->
        <div class="confirmation-card">
            <div class="confirm-icon">✔</div>
            <h3>Demande reçue avec succès !</h3>
            <p>Merci <strong><?php echo $submitted_data['prenom']; ?> <?php echo $submitted_data['nom']; ?></strong>, votre demande d'ouverture de compte a bien été enregistrée.</p>
            <div class="confirm-details">
                <div class="confirm-row"><span>Email :</span><span><?php echo $submitted_data['email']; ?></span></div>
                <div class="confirm-row"><span>Téléphone :</span><span><?php echo $submitted_data['telephone']; ?></span></div>
                <div class="confirm-row"><span>CIN :</span><span><?php echo $submitted_data['cin']; ?></span></div>
                <div class="confirm-row"><span>Ville :</span><span><?php echo $submitted_data['ville']; ?></span></div>
                <div class="confirm-row"><span>Type de compte :</span><span><?php echo $submitted_data['type_compte']; ?></span></div>
                <div class="confirm-row"><span>Revenu mensuel :</span><span><?php echo $submitted_data['revenu']; ?> MAD</span></div>
                <?php if (!empty($submitted_data['message'])): ?>
                <div class="confirm-row full"><span>Message :</span><span><?php echo $submitted_data['message']; ?></span></div>
                <?php endif; ?>
            </div>
            <p class="confirm-note">Un conseiller AtlasBank vous contactera à l'adresse <strong><?php echo $submitted_data['email']; ?></strong> dans les meilleurs délais.</p>
            <a href="#formulaire" class="btn btn-primary" onclick="window.location.reload()">Nouvelle demande</a>
        </div>

        <?php elseif (!empty($error_message)): ?>
        <div class="alert-error">
            <strong>Erreur :</strong> <?php echo $error_message; ?>
        </div>
        <?php endif; ?>

        <?php if (empty($success_message)): ?>
        <form class="form-card" method="POST" action="#formulaire" novalidate>
            <div class="form-section-title">Informations personnelles</div>
            <div class="form-grid">
                <div class="form-group">
                    <label for="nom">Nom <span class="req">*</span></label>
                    <input type="text" id="nom" name="nom" placeholder="El Mansouri" required />
                </div>
                <div class="form-group">
                    <label for="prenom">Prénom <span class="req">*</span></label>
                    <input type="text" id="prenom" name="prenom" placeholder="Youssef" required />
                </div>
                <div class="form-group">
                    <label for="email">Adresse e-mail <span class="req">*</span></label>
                    <input type="email" id="email" name="email" placeholder="youssef@email.com" required />
                </div>
                <div class="form-group">
                    <label for="telephone">Téléphone <span class="req">*</span></label>
                    <input type="tel" id="telephone" name="telephone" placeholder="+212 6XX XXX XXX" required />
                </div>
                <div class="form-group">
                    <label for="cin">CIN / Pièce d'identité <span class="req">*</span></label>
                    <input type="text" id="cin" name="cin" placeholder="AB123456" required />
                </div>
                <div class="form-group">
                    <label for="adresse">Adresse complète <span class="req">*</span></label>
                    <input type="text" id="adresse" name="adresse" placeholder="12, Rue Hassan II" required />
                </div>
                <div class="form-group">
                    <label for="ville">Ville <span class="req">*</span></label>
                    <select id="ville" name="ville" required>
                        <option value="" disabled selected>Sélectionnez votre ville</option>
                        <option>Casablanca</option>
                        <option>Rabat</option>
                        <option>Marrakech</option>
                        <option>Fès</option>
                        <option>Tanger</option>
                        <option>Agadir</option>
                        <option>Meknès</option>
                        <option>Oujda</option>
                        <option>Autre</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="profession">Profession <span class="req">*</span></label>
                    <input type="text" id="profession" name="profession" placeholder="Ingénieur, médecin, commerçant..." required />
                </div>
            </div>

            <div class="form-section-title">Informations financières</div>
            <div class="form-grid">
                <div class="form-group">
                    <label for="revenu">Revenu mensuel net (MAD) <span class="req">*</span></label>
                    <input type="number" id="revenu" name="revenu" placeholder="Ex : 8500" min="0" required />
                </div>
                <div class="form-group">
                    <label for="type_compte">Type de compte souhaité <span class="req">*</span></label>
                    <select id="type_compte" name="type_compte" required>
                        <option value="" disabled selected>Choisissez un type</option>
                        <option value="Compte Courant">Compte Courant</option>
                        <option value="Compte Épargne">Compte Épargne</option>
                        <option value="Compte Professionnel">Compte Professionnel</option>
                    </select>
                </div>
                <div class="form-group full-width">
                    <label for="message">Message ou remarques (optionnel)</label>
                    <textarea id="message" name="message" rows="4" placeholder="Précisez vos besoins, questions ou informations supplémentaires..."></textarea>
                </div>
            </div>

            <div class="form-footer">
                <label class="checkbox-label">
                    <input type="checkbox" required />
                    J'accepte les <a href="#">conditions générales</a> et la <a href="#">politique de confidentialité</a> d'AtlasBank.
                </label>
                <button type="submit" class="btn btn-primary btn-submit">Soumettre ma demande</button>
            </div>
        </form>
        <?php endif; ?>
    </div>
</section>

<!-- ========== CONTACT ========== -->
<section class="section section-alt" id="contact">
    <div class="container">
        <div class="section-header">
            <p class="section-eyebrow">Nous sommes là</p>
            <h2 class="section-title">Contactez-nous</h2>
        </div>
        <div class="contact-grid">
            <div class="contact-item">
                <span class="contact-icon">📍</span>
                <h4>Siège social</h4>
                <p>101, Boulevard Zerktouni<br>Casablanca 20000, Maroc</p>
            </div>
            <div class="contact-item">
                <span class="contact-icon">📞</span>
                <h4>Centre d'appels</h4>
                <p>0801 00 48 00<br>Lundi–Vendredi : 8h–20h</p>
            </div>
            <div class="contact-item">
                <span class="contact-icon">✉️</span>
                <h4>E-mail</h4>
                <p>contact@atlasbank.ma<br>assistance@atlasbank.ma</p>
            </div>
        </div>
    </div>
</section>

<!-- ========== FOOTER ========== -->
<footer class="footer">
    <div class="container footer-inner">
        <div class="footer-brand">
            <a href="#top" class="logo logo-light">
                <span class="logo-icon">⬡</span>
                <span class="logo-text">Atlas<strong>Bank</strong></span>
            </a>
            <p>Banque agréée par Bank Al-Maghrib.<br>RC : 123456 – Casablanca</p>
        </div>
        <div class="footer-links">
            <div class="footer-col">
                <h5>Particuliers</h5>
                <a href="#">Comptes courants</a>
                <a href="#">Épargne</a>
                <a href="#">Crédits</a>
                <a href="#">Assurances</a>
            </div>
            <div class="footer-col">
                <h5>Entreprises</h5>
                <a href="#">Compte pro</a>
                <a href="#">Financement</a>
                <a href="#">Commerce international</a>
            </div>
            <div class="footer-col">
                <h5>AtlasBank</h5>
                <a href="#">À propos</a>
                <a href="#">Carrières</a>
                <a href="#">Presse</a>
                <a href="#">Conformité</a>
            </div>
        </div>
    </div>
    <div class="footer-bottom container">
        <p>© 2025 AtlasBank S.A. Tous droits réservés. — Agréée par Bank Al-Maghrib sous le n°XX/YYYY.</p>
        <div class="footer-legal">
            <a href="#">Mentions légales</a>
            <a href="#">Politique de confidentialité</a>
            <a href="#">Cookies</a>
        </div>
    </div>
</footer>

<script>
    // Burger menu mobile
    const burger = document.getElementById('burger');
    const mobileNav = document.getElementById('mobileNav');
    burger.addEventListener('click', () => {
        mobileNav.classList.toggle('open');
        burger.classList.toggle('active');
    });

    // Fermeture automatique au clic sur un lien
    mobileNav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            mobileNav.classList.remove('open');
            burger.classList.remove('active');
        });
    });

    // Scroll pour activer les liens nav
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            if (window.scrollY >= section.offsetTop - 100) {
                current = section.getAttribute('id');
            }
        });
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });
</script>
</body>
</html>