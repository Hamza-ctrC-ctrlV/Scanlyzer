<?php

require_once 'config.php';

$success_message = "";
$error_message   = "";
$submitted_data  = [];

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // Connexion MySQL sans sécurité (intentionnel pour les tests)
    $conn = new mysqli($host, $username, $password, $dbname);

    if ($conn->connect_error) {
        $error_message = "Erreur de connexion : " . $conn->connect_error;
    } else {
        // Récupération des données SANS sanitisation (vulnérable XSS)
        $nom        = $_POST['nom'];
        $prenom     = $_POST['prenom'];
        $email      = $_POST['email'];
        $telephone  = $_POST['telephone'];
        $cin        = $_POST['cin'];
        $adresse    = $_POST['adresse'];
        $ville      = $_POST['ville'];
        $profession = $_POST['profession'];
        $revenu     = $_POST['revenu'];
        $type_compte= $_POST['type_compte'];
        $message    = $_POST['message'];

        // Requête SQL non sécurisée (pas de prepared statements — intentionnel)
        $sql = "INSERT INTO demandes (nom, prenom, email, telephone, cin, adresse, ville, profession, revenu, type_compte, message, date_demande)
                VALUES ('$nom', '$prenom', '$email', '$telephone', '$cin', '$adresse', '$ville', '$profession', '$revenu', '$type_compte', '$message', NOW())";

        if ($conn->query($sql) === TRUE) {
            $submitted_data = [
                'nom'        => $nom,
                'prenom'     => $prenom,
                'email'      => $email,
                'telephone'  => $telephone,
                'cin'        => $cin,
                'adresse'    => $adresse,
                'ville'      => $ville,
                'profession' => $profession,
                'revenu'     => $revenu,
                'type_compte'=> $type_compte,
                'message'    => $message,
            ];
            $success_message = "Votre demande a été soumise avec succès.";
        } else {
            $error_message = "Erreur SQL : " . $conn->error;
        }
        $conn->close();
    }
}