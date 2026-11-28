# FoodShare Android App – Design Reference

Static design reference for the FoodShare mobile app (donors and recipient organisations).
Visual references only: all names and numbers are **sample data**, and there is no app logic.

## Contents
- `pages/` – 7 standalone HTML screens (360 x 800). Open `01-sign-in.html` in a browser; the main buttons and bottom bar link between screens.
- `screenshots/` – a PNG of every screen (2x) and `overview.png` with all screens side by side.
- `logo/` – logo and app icon (SVG and PNG).

## Screens (SRS section 4.1)
01 Sign in / up (role: Donor or Recipient) · 02 Donor home (estimate + donations) · 03 Create donation · 04 Donation status · 05 Recipient inbox (accept / decline) · 06 Recipient profile · 07 Activity (notifications and summary)

## Design tokens
| Token | Value |
|---|---|
| Background | `#faf6f1` |
| Header / ink | `#2b1d17` |
| Primary (terracotta) | `#c4452a` |
| Soft highlight | `#fdeee6` (text `#a3361d`) |
| Card border | `#eadfd6` |
| Muted text | `#6b5b52` |
| Font | Inter (400-800) |

Predictions are always labelled ESTIMATE. Only a confirmed quantity can be offered. Touch targets are at least 44 px. FoodShare is decision support only.
