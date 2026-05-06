from flask import Flask, jsonify, send_from_directory, request
import requests
import csv
import io
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

MAILJET_API_KEY    = os.environ.get('MAILJET_API_KEY', '3b7ed6fa7e4d7e777bb144c487625b06')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY', '8a3a0f2e26c51aadaacfcd250b3126cf')
MJ_AUTH = (MAILJET_API_KEY, MAILJET_SECRET_KEY)
MJ_BASE = "https://api.mailjet.com/v3/REST"

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1N1lO3PdUqX9U4chc1sZXpP_zzfHYwXyfzpEXO4BxYWs"
    "/export?format=csv"
)

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzoRuw5zraZ_g-g3BioEbReo-m_e_N_glPikd8eJrGmsCe-Pr__cjR4_UX84ZxudQhR/exec"

MJML_BASE = """<mjml dir="ltr" lang="en" owa="desktop" version="4.14.1">
  <mj-head>
    <mj-font href="https://fonts.googleapis.com/css2?family=arial:wght@300;400;500;700;800;900" name="arial"></mj-font>
    <mj-font href="https://fonts.googleapis.com/css2?family=Josefin%20Sans:wght@300;400;500;700;800;900" name="Josefin Sans, Arial, sans-serif"></mj-font>
    <mj-preview></mj-preview>
  </mj-head>
  <mj-body background-color="#ffffff" color="#8b94a7" font-family="Josefin Sans, Arial, sans-serif">
    <mj-section background-color="#ffffff" background-repeat="repeat" background-size="auto" padding="0px 0px 0px 0px" vertical-align="top">
      <mj-column>
        <mj-image align="center" alt="" border="none" container-background-color="#e0d3c3" height="auto" padding="10px 25px 10px 25px" src="https://sjqzn.mjt.lu/img2/sjqzn/519a4db6-cda9-4e32-8e6f-608386b2fadd/content" target="_blank" title="" width="200px"></mj-image>
      </mj-column>
    </mj-section>
    <mj-section background-color="#f4f4f4" background-repeat="repeat" background-size="auto" padding="5px 0px 5px 0px" vertical-align="top">
      <mj-column>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="font-family:Josefin Sans, sans-serif;font-size:30px;font-weight:bold;text-align:center;color:#000000;line-height:40px;letter-spacing:0px;margin:20px 40px 10px 40px">EVENT_TITLE</p>
        </mj-text>
        <mj-image align="center" alt="" border-radius="10px" border="none" height="auto" padding-bottom="15px" padding-left="25px" padding-right="25px" padding-top="5px" padding="10px 25px" src="EVENT_IMAGE" target="_blank" title="" width="350px"></mj-image>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="font-family:Josefin Sans;font-size:23px;font-weight:normal;text-align:center;color:#000000;line-height:30px;letter-spacing:0px;margin:5px 20px"><strong>EVENT_DATE</strong></p>
          <p style="font-family:Josefin Sans, sans-serif;font-size:20px;font-weight:normal;text-align:center;color:#000000;line-height:30px;letter-spacing:0px;margin:5px 30px">EVENT_DESCRIPTION</p>
        </mj-text>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 10px; margin-bottom: 5px; margin-left: 10px;">
            <a href="SIGNUP_LINK1" style="background-color:#FFFFFF;color:#000000;border:1px solid #000000;border-radius:10px;padding:10px 20px;text-decoration:none;font-family:Josefin Sans, sans-serif;font-size:20px;font-weight:bold;display:inline-block">SIGNUP_TEXT1</a>
          </p>
        </mj-text>
        BUTTON2_PLACEHOLDER
        <mj-divider border-color="#E6E6E6" border-style="solid" border-width="2px" padding="10px 25px" width="100%"></mj-divider>
      </mj-column>
    </mj-section>
    <mj-section background-color="#e0d3c3" background-repeat="repeat" background-size="auto" padding="15px 25px 5px 25px" vertical-align="top">
      <mj-column>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 5px;">
            <a href="mailto:info@cobyscafe.com?subject=An%20idea%20for%20meetups%2Fevents" style="display:inline-block;font-family:Josefin Sans, sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Submit an Event Idea</a>
          </p>
        </mj-text>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 0px;">
            <a href="https://www.cobyscafe.com/membership" style="display:inline-block;font-family:Josefin Sans, sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Become a Member</a>
          </p>
        </mj-text>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 0px;">
            <a href="https://www.cobyscafe.com/parties" style="display:inline-block;font-family:Josefin Sans, sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;">Host a Party</a>
          </p>
        </mj-text>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 0px;">
            <a href="https://www.google.com/maps/search/?api=1&query=Coby's+Cafe+101+Nickerson+St+Seattle+WA" style="display:inline-block;font-family:Josefin Sans, sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;" target="_blank" rel="noopener">Leave a Google Review</a>
          </p>
        </mj-text>
        <mj-social align="center" border-radius="25px" container-background-color="transparent" font-size="13px" icon-padding="7px 7px 7px 7px" icon-size="28px" mode="horizontal" text-mode="false">
          <mj-social-element background-color="#3B5998" href="https://www.facebook.com/people/Cobys-Cafe/61553537724188/" name="facebook-noshare" src="https://static.mailjet.com/ico-social/facebook.png"></mj-social-element>
          <mj-social-element background-color="#9585F4" href="https://www.instagram.com/cobys.dog.cafe/" name="instagram-noshare" src="https://static.mailjet.com/ico-social/instagram-colored.png"></mj-social-element>
        </mj-social>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" padding-bottom="0px" padding-top="0px" padding="0px 5px 0px 5px">
          <p style="text-align: center; margin: 10px 0;">
            <span style="font-size:12px;font-family:Josefin Sans;color:#131B20;">Coby's Cafe<br>101 Nickerson Street Building B Ste 200<br>Seattle, Washington 98109<br>www.cobyscafe.com</span>
          </p>
        </mj-text>
        <mj-text font-family="Verdana, Helvetica, Arial, sans-serif" padding-bottom="0px" padding-top="0px" padding="10px 25px">
          <p style="text-align: center; margin: 10px 0;">
            <span style="font-size:12px;font-family:Josefin Sans;color:#000000;">If you do not wish to receive further communication like this, </span>
            <a href="[[UNSUB_LINK_EN]]" target="_blank"><span style="font-size:12px;font-family:Josefin Sans;color:#ffffff;"><u>unsubscribe here</u></span></a>
          </p>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""

BUTTON2_MJML = """<mj-text font-family="Verdana, Helvetica, Arial, sans-serif" frameBorder="0" padding="0px" passport-element="html" width="100%">
          <head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {{ font-family: 'Josefin Sans', sans-serif; }}</style></head>
          <p style="text-align: center; margin-top: 10px; margin-left: 10px;">
            <a href="SIGNUP_LINK2" style="background-color:#FFFFFF;color:#000000;border:1px solid #000000;border-radius:10px;padding:10px 20px;text-decoration:none;font-family:Josefin Sans, sans-serif;font-size:20px;font-weight:bold;display:inline-block">SIGNUP_TEXT2</a>
          </p>
        </mj-text>"""



ALIASES = {
    'name':        ['event name'],
    'month':       ['month'],
    'date':        ['date'],
    'time':        ['time'],
    'desc':        ['description'],
    'signupText1': ['sign up text 1', 'signup text 1'],
    'signupLink1': ['sign up link 1', 'signup link 1', 'sign up link'],
    'signupText2': ['sign up text 2', 'signup text 2'],
    'signupLink2': ['sign up link 2', 'signup link 2'],
    'status':      ['status'],
    'image':       ['image'],
}


BASE_HTML = """<!doctype html><html lang="en" dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><title></title><!--[if !mso]><!--><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]--><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style type="text/css">#outlook a { padding:0; }
      body { margin:0;padding:0;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%; }
      table, td { border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt; }
      img { border:0;height:auto;line-height:100%; outline:none;text-decoration:none;-ms-interpolation-mode:bicubic; }
      p { display:block;margin:13px 0; }</style><!--[if mso]>
    <noscript>
    <xml>
    <o:OfficeDocumentSettings>
      <o:AllowPNG/>
      <o:PixelsPerInch>96</o:PixelsPerInch>
    </o:OfficeDocumentSettings>
    </xml>
    </noscript>
    <![endif]--><!--[if lte mso 11]>
    <style type="text/css">
      .mj-outlook-group-fix { width:100% !important; }
    </style>
    <![endif]--><!--[if !mso]><!--><link href="https://fonts.googleapis.com/css2?family=arial:wght@300;400;500;700;800;900" rel="stylesheet" type="text/css"><link href="https://fonts.googleapis.com/css2?family=Josefin%20Sans:wght@300;400;500;700;800;900" rel="stylesheet" type="text/css"><style type="text/css">@import url(https://fonts.googleapis.com/css2?family=arial:wght@300;400;500;700;800;900);
@import url(https://fonts.googleapis.com/css2?family=Josefin%20Sans:wght@300;400;500;700;800;900);</style><!--<![endif]--><style type="text/css">@media only screen and (min-width:480px) {
        .mj-column-per-100 { width:100% !important; max-width: 100%; }
      }</style><style media="screen and (min-width:480px)">.moz-text-html .mj-column-per-100 { width:100% !important; max-width: 100%; }</style><style type="text/css">[owa] .mj-column-per-100 { width:100% !important; max-width: 100%; }</style><style type="text/css">@media only screen and (max-width:479px) {
      table.mj-full-width-mobile { width: 100% !important; }
      td.mj-full-width-mobile { width: auto !important; }
    }</style><style type="text/css"></style></head><body style="word-spacing:normal;background-color:#ffffff;"><div style="background-color:#ffffff;" role="main" lang="en" dir="ltr"><!--[if mso | IE]><table align="center" border="0" cellpadding="0" cellspacing="0" class="" role="presentation" style="width:600px;" width="600" bgcolor="#ffffff" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#ffffff;background-color:#ffffff;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#ffffff;background-color:#ffffff;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:0px 0px 0px 0px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="center" style="background:#e0d3c3;font-size:0px;padding:10px 25px 10px 25px;word-break:break-word;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;border-spacing:0px;"><tbody><tr><td style="width:200px;"><img alt="" src="https://sjqzn.mjt.lu/img2/sjqzn/519a4db6-cda9-4e32-8e6f-608386b2fadd/content" style="border:none;display:block;outline:none;text-decoration:none;height:auto;width:100%;font-size:13px;" width="200" height="auto"></td></tr></tbody></table></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" role="presentation" style="width:600px;" width="600" bgcolor="#f4f4f4" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#f4f4f4;background-color:#f4f4f4;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#f4f4f4;background-color:#f4f4f4;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:5px 0px 5px 0px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
            font-family: 'Josefin Sans', sans-serif;
        }</style></head><p style="font-family:'Josefin Sans', sans-serif;font-size:30px;font-weight:bold;text-align:center;color:#000000;line-height:40px;letter-spacing:0px;margin:20px 40px 10px 40px">Cinco de Mayo Fiesta</p></div></td></tr><tr><td align="center" style="font-size:0px;padding:10px 25px;padding-top:5px;padding-right:25px;padding-bottom:15px;padding-left:25px;word-break:break-word;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;border-spacing:0px;"><tbody><tr><td style="width:350px;"><img alt="" src="https://sjqzn.mjt.lu/img2/sjqzn/1ef5c329-24ef-45e8-9010-9d1d6393531e/content" style="border:none;border-radius:10px;display:block;outline:none;text-decoration:none;height:auto;width:100%;font-size:13px;" width="350" height="auto"></td></tr></tbody></table></td></tr><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
            font-family: 'Josefin Sans', sans-serif;
        }</style></head><p style="font-family:'Josefin Sans';font-size:23px;font-weight:normal;text-align:center;color:#000000;line-height:30px;letter-spacing:0px;margin:5px 20px"><strong>May 1 | 6-8PM</strong><br></p><p style="font-family:'Josefin Sans', sans-serif;font-size:20px;font-weight:normal;text-align:center;color:#000000;line-height:30px;letter-spacing:0px;margin:5px 30px">Festive night with a taco bar for people,<br>dog tacos & pawgaritas, and photo ops!</p></div></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" role="presentation" style="width:600px;" width="600" bgcolor="#f4f4f4" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#f4f4f4;background-color:#f4f4f4;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#f4f4f4;background-color:#f4f4f4;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:5px 0px 5px 0px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:600px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
            font-family: 'Josefin Sans', sans-serif;
        }</style></head><p style="text-align: center; margin-top: 10px; margin-bottom: 5px; margin-left: 10px;"><a href="https://square.link/u/RmROzE8s" style="background-color:#FFFFFF;color:#000000;border:1px solid #000000;border-radius:10px;padding:10px 20px;text-decoration:none;font-family:'Josefin Sans', sans-serif;font-size:20px;font-weight:bold;display:inline-block;text-decoration:none">General Ticket</a></p></div></td></tr><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
            font-family: 'Josefin Sans', sans-serif;
        }</style></head><p style="text-align: center; margin-top: 10px; margin-left: 10px;"><a href="https://square.link/u/O3jhGhi1" style="background-color:#FFFFFF;color:#000000;border:1px solid #000000;border-radius:10px;padding:10px 20px;text-decoration:none;font-family:'Josefin Sans', sans-serif;font-size:20px;font-weight:bold;display:inline-block;text-decoration:none">Member Free Sign Up</a></p></div></td></tr><tr><td align="center" style="font-size:0px;padding:10px 25px;word-break:break-word;"><p style="border-top:solid 2px #E6E6E6;font-size:1px;margin:0px auto;width:100%;"></p><!--[if mso | IE]><table align="center" border="0" cellpadding="0" cellspacing="0" style="border-top:solid 2px #E6E6E6;font-size:1px;margin:0px auto;width:550px;" role="presentation" width="550px" ><tr><td style="height:0;line-height:0;"> &nbsp;
</td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><table align="center" border="0" cellpadding="0" cellspacing="0" class="" role="presentation" style="width:600px;" width="600" bgcolor="#e0d3c3" ><tr><td style="line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]--><div style="background:#e0d3c3;background-color:#e0d3c3;margin:0px auto;max-width:600px;"><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#e0d3c3;background-color:#e0d3c3;width:100%;"><tbody><tr><td style="direction:ltr;font-size:0px;padding:15px 25px 5px 25px;text-align:center;"><!--[if mso | IE]><table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td class="" style="vertical-align:top;width:550px;" ><![endif]--><div class="mj-column-per-100 mj-outlook-group-fix" style="font-size:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;width:100%;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="vertical-align:top;" width="100%"><tbody><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
      font-family: 'Josefin Sans', sans-serif;
    }

    @media (prefers-color-scheme: dark) {
      a.event-button {
        color: #ffffff !important;
        background-color: #333333 !important;
        border-color: #ffffff !important;
      }

      a.event-button:hover {
        background-color: #444444 !important;
      }
    }</style></head><p style="text-align: center; margin-top: 5px;"><a href="mailto:info@cobyscafe.com?subject=An%20idea%20for%20meetups%2Fevents&body=Hi%20Coby's%20Cafe%2C%0A%0AI%20have%20an%20idea%20for%20a%20meetup%20or%20event%3A%0A" class="event-button" style="display:inline-block;font-family:'Josefin Sans', sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;transition:background-color 0.3s ease;text-decoration:none" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='#ffffff'">Submit an Event Idea</a></p></div></td></tr><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
      font-family: 'Josefin Sans', sans-serif;
    }

    @media (prefers-color-scheme: dark) {
      a.event-button {
        color: #ffffff !important;
        background-color: #333333 !important;
        border-color: #ffffff !important;
      }

      a.event-button:hover {
        background-color: #444444 !important;
      }
    }</style></head><p style="text-align: center; margin-top: 0px;"><a href="https://www.cobyscafe.com/membership" class="link-button" style="display:inline-block;font-family:'Josefin Sans', sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;transition:background-color 0.3s ease;text-decoration:none" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='#ffffff'">Become a Member</a></p></div></td></tr><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
      font-family: 'Josefin Sans', sans-serif;
    }

    @media (prefers-color-scheme: dark) {
      a.event-button {
        color: #ffffff !important;
        background-color: #333333 !important;
        border-color: #ffffff !important;
      }

      a.event-button:hover {
        background-color: #444444 !important;
      }
    }</style></head><p style="text-align: center; margin-top: 0px;"><a href="https://www.cobyscafe.com/parties" class="link-button" style="display:inline-block;font-family:'Josefin Sans', sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;transition:background-color 0.3s ease;text-decoration:none" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='#ffffff'">Host a Party</a></p></div></td></tr><tr><td align="left" style="font-size:0px;padding:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><head><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans&display=swap" rel="stylesheet"><style>* {
      font-family: 'Josefin Sans', sans-serif;
    }
    @media (prefers-color-scheme: dark) {
      a.event-button {
        color: #ffffff !important;
        background-color: #333333 !important;
        border-color: #ffffff !important;
      }
      a.event-button:hover {
        background-color: #444444 !important;
      }
    }</style></head><p style="text-align: center; margin-top: 0px;"><a href="https://www.google.com/maps/search/?api=1&query=Coby's+Cafe+101+Nickerson+St+Seattle+WA" class="link-button" style="display:inline-block;font-family:'Josefin Sans', sans-serif;font-size:18px;font-weight:bold;text-decoration:none;padding:5px 10px;border-radius:8px;border:1px solid #2D2D2D;color:#2D2D2D;background-color:#ffffff;transition:background-color 0.3s ease;text-decoration:none" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='#ffffff'" target="_blank" rel="noopener">Leave a Google Review</a></p></div></td></tr><tr><td align="center" style="background:transparent;font-size:0px;padding:10px 25px;word-break:break-word;"><!--[if mso | IE]><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" ><tr><td><![endif]--><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="float:none;display:inline-table;"><tbody><tr><td aria-hidden="true" style="padding:4px;vertical-align:middle;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#3B5998;border-radius:25px;width:28px;"><tbody><tr><td style="padding:7px 7px 7px 7px;font-size:0;height:28px;vertical-align:middle;width:28px;"><a href="https://www.facebook.com/people/Cobys-Cafe/61553537724188/" target="_blank"><img alt="" height="28" src="https://static.mailjet.com/ico-social/facebook.png" style="border-radius:25px;display:block;" width="28"></a></td></tr></tbody></table></td></tr></tbody></table><!--[if mso | IE]></td><td><![endif]--><table align="center" border="0" cellpadding="0" cellspacing="0" role="presentation" style="float:none;display:inline-table;"><tbody><tr><td aria-hidden="true" style="padding:4px;vertical-align:middle;"><table border="0" cellpadding="0" cellspacing="0" role="presentation" style="background:#9585F4;border-radius:25px;width:28px;"><tbody><tr><td style="padding:7px 7px 7px 7px;font-size:0;height:28px;vertical-align:middle;width:28px;"><a href="https://www.instagram.com/cobys.dog.cafe/" target="_blank"><img alt="" height="28" src="https://static.mailjet.com/ico-social/instagram-colored.png" style="border-radius:25px;display:block;" width="28"></a></td></tr></tbody></table></td></tr></tbody></table><!--[if mso | IE]></td></tr></table><![endif]--></td></tr><tr><td align="left" style="font-size:0px;padding:0px 5px 0px 5px;padding-top:0px;padding-bottom:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><p style="text-align: center; margin: 10px 0; margin-top: 10px; margin-bottom: 10px;"><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#131B20;text-align:left">Coby's Cafe </span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:16px;font-family:Verdana;color:#000000;text-align:left"><br></span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#131B20;text-align:left">101 Nickerson Street Building B Ste 200 </span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:16px;font-family:Verdana;color:#000000;text-align:left"><br></span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#131B20;text-align:left">Seattle, Washington 98109 </span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:16px;font-family:Verdana;color:#000000;text-align:left"><br></span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#131B20;text-align:left">Get Directions </span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:16px;font-family:Verdana;color:#000000;text-align:left"><br></span><span style="text-align:center;line-height:15px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#131B20;text-align:left">www.cobyscafe.com</span></p></div></td></tr><tr><td align="left" style="font-size:0px;padding:10px 25px;padding-top:0px;padding-bottom:0px;word-break:break-word;"><div style="font-family:Verdana, Helvetica, Arial, sans-serif;font-size:13px;line-height:1;text-align:left;color:#000000;"><p style="text-align: center; margin: 10px 0; margin-top: 10px; margin-bottom: 10px;"><span style="text-align:center;line-height:16px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#000000;text-align:left">If you do not wish to receive further communication like this, </span><a href="[[UNSUB_LINK_EN]]" target="_blank" style="; text-decoration: none;"><span><span style="text-align:center;line-height:16px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#ffffff;text-align:left"><u>unsubscribe here</u></span></span></a><span style="text-align:center;line-height:16px;letter-spacing:normal;font-size:12px;font-family:'Josefin Sans';color:#ffffff;text-align:left">.</span></p></div></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></td></tr></tbody></table></div><!--[if mso | IE]></td></tr></table><![endif]--></div></body></html>"""

def get_col_index(headers):
    col = {}
    for key, alias_list in ALIASES.items():
        for alias in alias_list:
            if alias in headers:
                col[key] = headers.index(alias)
                break
    return col

def get_cell(row, col, key):
    idx = col.get(key)
    if idx is not None and idx < len(row):
        return row[idx].strip()
    return ''

def parse_csv(text):
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    col = get_col_index(headers)
    events = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        events.append({k: get_cell(row, col, k) for k in ALIASES})
    return events

def format_datetime(date, time_str):
    date = re.sub(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*', '', date, flags=re.IGNORECASE).strip()
    return f"{date} | {time_str}" if time_str else date

def get_base_html():
    return BASE_HTML, None

def fill_template(html, event):
    """Generate MJML for drag-and-drop editing in Mailjet."""
    name  = event['name']
    date  = format_datetime(event['date'], event['time'])
    desc  = event['desc']
    txt1  = event['signupText1'] or 'General Ticket'
    lnk1  = event['signupLink1'] if event['signupLink1'].startswith('http') else '#'
    txt2  = event['signupText2']
    lnk2  = event['signupLink2'] if event['signupLink2'].startswith('http') else ''
    image = event['image'] if event['image'] and event['image'].startswith('http') else 'https://sjqzn.mjt.lu/img2/sjqzn/1ef5c329-24ef-45e8-9010-9d1d6393531e/content'

    # Build button 2 if needed
    btn2 = BUTTON2_MJML.replace('SIGNUP_LINK2', lnk2).replace('SIGNUP_TEXT2', txt2) if txt2 and lnk2 else ''

    out = MJML_BASE
    out = out.replace('EVENT_TITLE', name)
    out = out.replace('EVENT_DATE', date)
    out = out.replace('EVENT_DESCRIPTION', desc)
    out = out.replace('EVENT_IMAGE', image)
    out = out.replace('SIGNUP_LINK1', lnk1)
    out = out.replace('SIGNUP_TEXT1', txt1)
    out = out.replace('BUTTON2_PLACEHOLDER', btn2)

    return out

def mark_done(event_name):
    try:
        requests.post(APPS_SCRIPT_URL, json={'eventName': event_name}, timeout=10)
    except:
        pass

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        return jsonify({'success': True, 'events': parse_csv(res.text)})
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

@app.route('/api/run', methods=['POST'])
def run_automation():
    try:
        res = requests.get(SHEET_CSV_URL, timeout=15)
        res.raise_for_status()
        events = parse_csv(res.text)
        new_events = [e for e in events if e['status'].lower() == 'new']

        if not new_events:
            return jsonify({'success': True, 'results': [], 'message': 'No new events found.'})

        results = []
        for event in new_events:
            try:
                filled = fill_template(None, event)
                filename = re.sub(r'[^a-zA-Z0-9]+', '_', event['name']) + '.mjml'
                mark_done(event['name'])
                results.append({
                    'name': event['name'],
                    'status': 'success',
                    'html': filled,
                    'filename': filename
                })
            except Exception as ex:
                results.append({'name': event['name'], 'status': 'error', 'error': str(ex)})

        return jsonify({'success': True, 'results': results})

    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500

if __name__ == '__main__':
    app.run(debug=False)
