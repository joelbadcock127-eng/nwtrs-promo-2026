#!/bin/bash
# Render end-card background PNGs + text layers + card segments (42-45).
set -e
cd "$(dirname "$0")"
mkdir -p cards segments
GOLD="#CCB268"
FPS=24
F5=fonts/Montserrat-500.ttf
F6=fonts/Montserrat-600.ttf
F7=fonts/Montserrat-700.ttf
F8=fonts/Montserrat-800.ttf
LOGO=/home/user/nwtrs-promo-2026/tenfifty-bakers-logo-transparent-4096px.png

# ---------- backgrounds ----------
# dark vignette base
convert -size 1920x1080 radial-gradient:'#171410'-'#070605' cards/bg_dark.png
# welcome card bg: darkened aurora frame
AUR=ai/aurora1_2k.mp4; [ -f "$AUR" ] || AUR=ai/aurora1.mp4
ffmpeg -v error -sseof -0.4 -i "$AUR" -frames:v 1 -y cards/aurora_frame.png
convert cards/aurora_frame.png -resize 1920x1080^ -gravity center -extent 1920x1080 \
  -blur 0x6 -modulate 55,85,100 -fill black -colorize 35% cards/bg_welcome.png

# ---------- text layer helper ----------
# centered multi-element cards drawn directly

# CARD 1: welcome (bg aurora)
convert cards/bg_welcome.png \
  -font $F6 -pointsize 30 -kerning 12 -fill "$GOLD" -gravity north \
  -annotate +0+330 "FROM 2027" \
  -font $F7 -pointsize 62 -kerning 6 -fill white \
  -annotate +0+420 "TEN FIFTY BAKERS JOINS THE" \
  -font $F8 -pointsize 74 -kerning 4 -fill "$GOLD" \
  -annotate +0+530 "NORTH WEST" \
  -annotate +0+640 "TRAIL RUNNING SERIES" \
  cards/card1.png

# CARD 2: offer
convert cards/bg_dark.png \
  -font $F6 -pointsize 30 -kerning 10 -fill "$GOLD" -gravity north \
  -annotate +0+250 "FOR NWTRS RUNNERS, FRIENDS & FAMILY" \
  -fill "$GOLD" -draw "rectangle 885,320 1035,324" \
  -font $F7 -pointsize 66 -kerning 3 -fill white \
  -annotate +0+470 "STAY 2 NIGHTS — 3RD NIGHT FREE" \
  -font $F5 -pointsize 30 -kerning 6 -fill '#D9D4C8' \
  -annotate +0+640 "BOOK THIS WEEK · STAY ANY TIME IN THE NEXT 12 MONTHS" \
  -font $F6 -pointsize 32 -kerning 6 -fill "$GOLD" \
  -annotate +0+710 "VALUED AT UP TO \$1,500" \
  cards/card2.png

# CARD 3: booking (with QR)
convert cards/bg_dark.png \
  -font $F8 -pointsize 78 -kerning 5 -fill white -gravity north \
  -annotate +0+330 "BOOK BY MIDNIGHT SUNDAY" \
  -font $F7 -pointsize 52 -kerning 8 -fill "$GOLD" \
  -annotate +0+490 "TENFIFTYBAKERS.COM.AU" \
  cards/card3_base.png
# QR panel: white rounded card + black QR + label
convert cards/qr_raw.png -resize 252x252 cards/qr_s.png
convert -size 300x352 xc:none -fill white -draw "roundrectangle 0,0 299,351 18,18" cards/qr_panel.png
convert cards/qr_panel.png cards/qr_s.png -gravity north -geometry +0+24 -composite \
  -font $F7 -pointsize 26 -kerning 6 -fill '#111111' -gravity south \
  -annotate +0+22 "SCAN TO BOOK" cards/qr_card.png
# gold chip with code
convert -size 560x92 xc:none -fill none -stroke "$GOLD" -strokewidth 3 \
  -draw "roundrectangle 2,2 557,89 14,14" \
  -font $F7 -pointsize 40 -kerning 10 -stroke none -fill white -gravity center \
  -annotate +0+2 "USE CODE: NWTRS" cards/chip.png
convert cards/card3_base.png cards/chip.png -gravity north -geometry +0+640 -composite cards/card3.png

# CARD 4: logo end card
convert "$LOGO" -resize 1250x cards/logo_w.png
convert cards/bg_dark.png cards/logo_w.png -gravity center -geometry +0-60 -composite \
  -font $F5 -pointsize 30 -kerning 14 -fill '#D9D4C8' -gravity north \
  -annotate +0+640 "BAKERS BEACH · TASMANIA" \
  -font $F5 -pointsize 26 -kerning 8 -fill "$GOLD" \
  -annotate +0+720 "TENFIFTYBAKERS.COM.AU  ·  CODE NWTRS" \
  -font $F5 -pointsize 22 -kerning 6 -fill '#8F887A' \
  -annotate +0+790 "MUSIC: “SLOW AGAIN” — WRITTEN FOR TEN FIFTY" \
  cards/card4.png

# ---------- card segments with gentle zoom + fades ----------
seg () { # img dur out extra
  local img=$1 dur=$2 out=$3 fadeout=$4
  local d=$(python3 -c "print(round($dur*24))")
  local vf="scale=3840:2160,zoompan=z='1.0+0.035*on/${d}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=${d}:s=1920x1080:fps=24"
  if [ -n "$fadeout" ]; then vf="$vf,fade=t=out:st=$fadeout:d=1.6"; fi
  ffmpeg -v error -loop 1 -framerate 24 -i "$img" -vf "$vf" -r 24 -pix_fmt yuv420p \
    -c:v libx264 -crf 17 -preset medium -t "$dur" -an -y "$out"
}
seg cards/card1.png 8.4  segments/042.mp4
seg cards/card2.png 9.9  segments/043.mp4
seg cards/card3.png 9.3  segments/044.mp4
seg cards/card4.png 7.92 segments/045.mp4 6.2
echo CARDS-DONE
