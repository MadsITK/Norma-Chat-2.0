# -*- coding: utf-8 -*-
# Norma Robot HTTP Service
# Python 2.7 / NAOqi
# TTS + Tablet + Gesture-cycling + BaseHTTPServer (threaded)
# ==========================================================

from __future__ import print_function

import os
import sys
import json
import time
import base64
import threading

try:
    # Python 2.7
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    import SocketServer as socketserver
except Exception:
    # Fallback names (shouldn't be used in Python 2.7 environment)
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import socketserver

try:
    from naoqi import ALProxy
except Exception as _e:
    # Delay import error until first use to allow module import on non-robot hosts
    ALProxy = None

# ==========================================================
# 1: KONFIGURATION
# ==========================================================
# Tryk på Norma's maveknap hvis du ikke tror hun er på den rigtige IP adresse. Ændr til hvad hun siger!
ROBOT_IP   = "192.168.1.156" # This should not be hardcoded
ROBOT_PORT = 9559

# Lokal intro-billede til tablet (valgfrit). Hvis tom eller fil ikke findes, springes intro over.
LOCAL_IMAGE_PATH = r""

# Gestures (samme rækkefølge som tidligere script)
GESTURES = [
    "hello",
    "happy",
    "calm",
    "enthusiastic",
    "beseech",
    "cool",
    "bow",
    "body language",
    "exalted",
    "but",
]

# ==========================================================
# 2: SERVICE KLASSE
# ==========================================================
class NormaRobotService(object):
    """Thread-safe NAOqi service wrapper for Norma.

    Metoder:
      - say(text, gesture=None)
      - play_gesture(gesture_name)
      - show_tablet_image(image_path)
      - show_tablet_html(html_content)
      - hide_tablet()
      - get_status()
    """

    def __init__(self, robot_ip, robot_port):
        if ALProxy is None:
            raise RuntimeError("NAOqi ALProxy ikke tilgængelig på dette system")
        self.robot_ip = robot_ip
        self.robot_port = int(robot_port)
        self._lock = threading.RLock()
        self._interaction_count = 0

        # Opret NAOqi proxies
        self._tts = ALProxy("ALTextToSpeech",    self.robot_ip, self.robot_port)
        self._anim = ALProxy("ALAnimationPlayer", self.robot_ip, self.robot_port)
        self._tablet = ALProxy("ALTabletService",  self.robot_ip, self.robot_port)

        # Tablet intro + velkomst (bevar eksisterende funktionalitet)
        try:
            self._startup_intro()
        except Exception as e:
            self._log("Intro fejl: %s" % (e,))

    # ------------------ interne hjælpefunktioner ------------------
    def _log(self, msg):
        try:
            # Simple timestamped log to stdout (compatible with py2)
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            print("[%s] %s" % (ts, msg))
        except Exception:
            pass

    def _ensure_unicode(self, text):
        if isinstance(text, unicode):
            return text
        elif isinstance(text, str):
            # bytes -> decode as utf-8, replace errors
            return text.decode('utf-8', 'replace')
        else:
            return unicode(text)

    def _startup_intro(self):
        with self._lock:
            # Kør lille animation
            try:
                self._anim.runTag("cloud")
            except Exception:
                pass

            # Vis intro-billede hvis tilgængeligt
            if LOCAL_IMAGE_PATH and os.path.exists(LOCAL_IMAGE_PATH):
                try:
                    data = open(LOCAL_IMAGE_PATH, 'rb').read()
                    b64 = base64.b64encode(data)
                    html = (
                        "<html><head>\n"
                        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=2.0\"/>\n"
                        "<style>body{margin:0;padding:0;height:100vh;display:flex;justify-content:center;align-items:center;background:#fff;}"
                        "img{max-width:200%;max-height:200%;}</style></head><body>"
                        "<img src=\"data:image/png;base64,%s\"/></body></html>" % b64
                    )
                    uri = "data:text/html;base64," + base64.b64encode(html)
                    try:
                        self._tablet.hideWebview()
                    except Exception:
                        pass
                    self._tablet.showWebview(uri)
                except Exception as e:
                    self._log("Kunne ikke vise intro-billede: %s" % (e,))

            # Velkomst-tts
            try:
                self._tts.say(self._to_tts_bytes(self._ensure_unicode(u"Jeg hedder Norma og du kan snakke med mig")))
            except Exception as e:
                self._log("Kunne ikke sige velkomst: %s" % (e,))

    def _to_tts_bytes(self, utext):
        # ALTextToSpeech i Python 2 kan tage bytes (utf-8)
        if isinstance(utext, unicode):
            return utext.encode('utf-8')
        elif isinstance(utext, str):
            # antag allerede utf-8
            return utext
        else:
            return unicode(utext).encode('utf-8')

    def _cycle_gesture_name(self):
        # Hver anden interaktion -> vælg gesture baseret på tæller
        if self._interaction_count % 2 == 0:
            idx = self._interaction_count % len(GESTURES) if GESTURES else 0
            return GESTURES[idx] if GESTURES else None
        return None

    # ------------------ offentlige service-metoder ------------------
    def say(self, text, gesture=None):
        with self._lock:
            utext = self._ensure_unicode(text)
            self._interaction_count += 1
            # TTS
            self._tts.say(self._to_tts_bytes(utext))
            # Gesture
            g = gesture or self._cycle_gesture_name()
            if g:
                try:
                    self._anim.runTag(g)
                except Exception as e:
                    self._log("Gesture fejl (%s): %s" % (g, e))
            return {
                'spoken_text': utext,
                'gesture': g,
                'interaction_count': self._interaction_count,
            }

    def play_gesture(self, gesture_name):
        with self._lock:
            if not gesture_name:
                raise ValueError('gesture_name mangler')
            self._anim.runTag(gesture_name)
            return {'played': gesture_name}

    def show_tablet_image(self, image_path):
        with self._lock:
            if not image_path or not os.path.exists(image_path):
                raise IOError('Billedfil ikke fundet: %s' % (image_path,))
            data = open(image_path, 'rb').read()
            b64 = base64.b64encode(data)
            html = "<html><body style=\"margin:0;display:flex;align-items:center;justify-content:center;background:#fff\">" \
                   "<img style=\"max-width:200%;max-height:200%\" src=\"data:image/png;base64,%s\"/>" \
                   "</body></html>" % b64
            uri = "data:text/html;base64," + base64.b64encode(html)
            try:
                self._tablet.hideWebview()
            except Exception:
                pass
            self._tablet.showWebview(uri)
            return {'shown_image': os.path.abspath(image_path)}

    def show_tablet_html(self, html_content):
        with self._lock:
            if html_content is None:
                raise ValueError('html_content mangler')
            if isinstance(html_content, unicode):
                html_bytes = html_content.encode('utf-8')
            else:
                html_bytes = str(html_content)
            uri = "data:text/html;base64," + base64.b64encode(html_bytes)
            try:
                self._tablet.hideWebview()
            except Exception:
                pass
            self._tablet.showWebview(uri)
            return {'html_length': len(html_bytes)}

    def hide_tablet(self):
        with self._lock:
            self._tablet.hideWebview()
            return {'hidden': True}

    def get_status(self):
        with self._lock:
            return {
                'ip': self.robot_ip,
                'port': self.robot_port,
                'interaction_count': self._interaction_count,
            }

# ==========================================================
# 3: HTTP SERVER (threaded)
# ==========================================================
class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class ApiHandler(BaseHTTPRequestHandler):
    # Reference til service injiceres på modul-niveau
    service = None

    def _send_json(self, code, payload):
        data = json.dumps(payload)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != '/api/command':
            self._send_json(404, {"status": "error", "message": "Not Found"})
            return
        length = int(self.headers.get('Content-Length') or 0)
        try:
            body = self.rfile.read(length) if length > 0 else '{}'
            try:
                payload = json.loads(body)
            except Exception:
                self._send_json(400, {"status": "error", "message": "Ugyldig JSON"})
                return
            cmd = payload.get('command')
            params = payload.get('params') or {}
            if not ApiHandler.service:
                self._send_json(500, {"status": "error", "message": "Service ikke initialiseret"})
                return

            try:
                result = self._dispatch(cmd, params)
                self._send_json(200, {"status": "success", "data": result})
            except Exception as e:
                self._send_json(500, {"status": "error", "message": str(e)})
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def do_GET(self):
        if self.path == '/api/status':
            try:
                result = ApiHandler.service.get_status() if ApiHandler.service else {}
                self._send_json(200, {"status": "success", "data": result})
            except Exception as e:
                self._send_json(500, {"status": "error", "message": str(e)})
            return
        self._send_json(404, {"status": "error", "message": "Not Found"})

    def log_message(self, fmt, *args):
        # Quieter server logs: print to stdout
        try:
            sys.stdout.write("SERVER: " + (fmt % args) + "\n")
        except Exception:
            pass

    def _dispatch(self, cmd, params):
        if not cmd:
            raise ValueError('command mangler')
        svc = ApiHandler.service
        c = cmd.strip().lower()
        if c == 'say':
            text = params.get('text')
            gesture = params.get('gesture')
            if text is None:
                raise ValueError('params.text mangler')
            return svc.say(text, gesture)
        elif c == 'play_gesture':
            gesture_name = params.get('gesture_name') or params.get('gesture')
            return svc.play_gesture(gesture_name)
        elif c == 'show_tablet_image':
            image_path = params.get('image_path')
            return svc.show_tablet_image(image_path)
        elif c == 'show_tablet_html':
            html_content = params.get('html') or params.get('html_content')
            return svc.show_tablet_html(html_content)
        elif c == 'hide_tablet':
            return svc.hide_tablet()
        elif c == 'get_status':
            return svc.get_status()
        else:
            raise ValueError('Ukendt kommando: %s' % cmd)

# ==========================================================
# 4: MAIN
# ==========================================================

def run_server():
    # Initialiser service
    service = NormaRobotService(ROBOT_IP, ROBOT_PORT)
    ApiHandler.service = service

    # Start server på port 8080
    server_address = ('', 8080)
    httpd = ThreadedHTTPServer(server_address, ApiHandler)
    print("Norma HTTP service lytter på port 8080 ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopper HTTP service...")
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass

if __name__ == '__main__':
    run_server()

