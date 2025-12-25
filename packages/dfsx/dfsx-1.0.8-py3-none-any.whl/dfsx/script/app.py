from fastapi import FastAPI, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
import asyncio
import json
import os
import re
import subprocess
from typing import Optional

app = FastAPI()

verifieds_path = os.path.join(os.path.dirname(__file__), "verifieds.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open(os.path.join(os.path.dirname(__file__), "values.json"), "r") as f:
    config = json.load(f)

API_ID = config["api_id"]
API_HASH = config["api_hash"]
PROCESS_NAME = config["process_name"]

current_client = None
current_phone = None
phone_code_hash = None

def load_verifieds():
    if os.path.exists(verifieds_path):
        with open(verifieds_path, "r") as f:
            return json.load(f)
    return []
    
def save_verifieds(data):
    with open(verifieds_path, "w") as f:
        json.dump(data, f)
        
def restart_bot():
    try:
        result = subprocess.run(
            ["supervisorctl", "restart", PROCESS_NAME],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return str(e)
        
@app.get("/allow")
def allow(id: int = Query(...)):
    verifieds = load_verifieds()
    if id not in verifieds:
        verifieds.append(id)
        save_verifieds(verifieds)
        restart_msg = restart_bot()
        return {"status": "success", "message": f"Chat ID {id} allowed.", "restart": restart_msg}
    return {"status": "already", "message": f"Chat ID {id} is already allowed."}

@app.get("/disallow")
def disallow(id: int = Query(...)):
    verifieds = load_verifieds()
    if id in verifieds:
        verifieds.remove(id)
        save_verifieds(verifieds)
        restart_msg = restart_bot()
        return {"status": "success", "message": f"Chat ID {id} disallowed.", "restart": restart_msg}
    return {"status": "already", "message": f"Chat ID {id} already disallowed."}

@app.get("/api/values")
async def get_api_values():
    try:
        with open(os.path.join(os.path.dirname(__file__), "values.json"), "r") as f:
            config = json.load(f)
        return JSONResponse(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load values: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
        <title>Account Updator</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                animation: backgroundShift 10s ease-in-out infinite alternate;
            }
            
            @keyframes backgroundShift {
                0% { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
                100% { background: linear-gradient(135deg, #764ba2 0%, #667eea 100%); }
            }
            
            .header {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 20px 0;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .header h1 {
                color: white;
                text-align: left;
                margin-left: 50px;
                font-size: 2.5rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                animation: titleGlow 3s ease-in-out infinite alternate;
            }
            
            @keyframes titleGlow {
                0% { text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3); }
                100% { text-shadow: 2px 2px 20px rgba(255, 255, 255, 0.5); }
            }
            
            .container {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 50px 20px;
                flex-direction: column;
                gap: 30px;
            }
            
            .update-section {
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                width: 100%;
                max-width: 450px;
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                animation: containerFloat 6s ease-in-out infinite;
                transform-origin: center;
            }
            
            @keyframes containerFloat {
                0%, 100% { transform: translateY(0px) scale(1); }
                50% { transform: translateY(-10px) scale(1.02); }
            }
            
            .update-section h2 {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
                font-size: 1.8rem;
                font-weight: 600;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .form-group {
                margin-bottom: 25px;
                animation: slideInUp 0.6s ease-out;
            }
            
            @keyframes slideInUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #555;
                font-weight: 500;
                font-size: 0.95rem;
            }
            
            .form-group input {
                width: 100%;
                padding: 15px;
                border: 2px solid #e1e5e9;
                border-radius: 12px;
                font-size: 16px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                background: rgba(255, 255, 255, 0.9);
                outline: none;
            }
            
            .form-group input:focus {
                border-color: #667eea;
                background: white;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                transform: translateY(-2px);
            }
            
            .btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                text-transform: uppercase;
                letter-spacing: 1px;
                position: relative;
                overflow: hidden;
            }
            
            .btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }
            
            .btn:hover::before {
                left: 100%;
            }
            
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }
            
            .btn:active {
                transform: translateY(-1px);
            }
            
            .btn:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .hidden {
                display: none;
            }
            
            .success-message {
                background: linear-gradient(45deg, #4CAF50, #45a049);
                color: white;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                margin-top: 20px;
                animation: successPulse 2s ease-in-out infinite;
            }
            
            @keyframes successPulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .error-message {
                background: linear-gradient(45deg, #f44336, #d32f2f);
                color: white;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                margin-top: 20px;
                animation: shake 0.6s ease-in-out;
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            .response-box {
                background: #000;
                color: #0f0;
                padding: 15px;
                border-radius: 12px;
                margin-top: 20px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .particles {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
            }
            
            .particle {
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(255, 255, 255, 0.7);
                border-radius: 50%;
                animation: float 6s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0; }
                10%, 90% { opacity: 1; }
                50% { transform: translateY(-100px) rotate(180deg); }
            }
        </style>
    </head>
    <body>
        <div class="particles" id="particles"></div>
        
        <header class="header">
            <h1>टेलर साहब</h1>
        </header>
        
        <div class="container">
            <div class="update-section">
                <h2>Update Section</h2>
                
                <form id="authForm">
                    <div class="form-group" id="phoneGroup">
                        <label for="phone">Enter Telegram Account Number</label>
                        <input type="tel" id="phone" name="phone" placeholder="+918209004143" required>
                    </div>
                    
                    <div class="form-group" id="phoneButtonGroup">
                        <button type="button" class="btn" id="sendOtpBtn">Send OTP</button>
                    </div>
                    
                    <div class="form-group hidden" id="otpGroup">
                        <label for="otp">Enter OTP</label>
                        <input type="text" id="otp" name="otp" placeholder="12345" required>
                    </div>
                    
                    <div class="form-group hidden" id="otpButtonGroup">
                        <button type="button" class="btn" id="verifyOtpBtn">Verify</button>
                    </div>
                    
                    <div class="form-group hidden" id="passwordGroup">
                        <label for="password">Enter Password (2FA)</label>
                        <input type="password" id="password" name="password" placeholder="Your 2FA Password" required>
                    </div>
                    
                    <div class="form-group hidden" id="passwordButtonGroup">
                        <button type="button" class="btn" id="verifyPasswordBtn">Verify Password</button>
                    </div>
                </form>
                
                <div id="messageArea"></div>
            </div>
            
            <div class="update-section">
                <h2>APIs Update</h2>
                
                <form id="apiForm">
                    <div class="form-group">
                        <label for="apiId">API ID</label>
                        <input type="text" id="apiId" name="apiId" placeholder="25996497" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="apiHash">API Hash</label>
                        <input type="text" id="apiHash" name="apiHash" placeholder="a2804f75fbd6ddd7e6cdee6edb022a9e" required>
                    </div>
                    
                    <div class="form-group">
                        <button type="button" class="btn" id="updateApiBtn">Update</button>
                    </div>
                </form>
                
                <div id="apiResponseArea"></div>
            </div>
        </div>
        
        <script>
            // Create animated particles
            function createParticles() {
                const particlesContainer = document.getElementById('particles');
                const numberOfParticles = 50;
                
                for (let i = 0; i < numberOfParticles; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.animationDelay = Math.random() * 6 + 's';
                    particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
                    particlesContainer.appendChild(particle);
                }
            }
            
            createParticles();
            
            // Load current API values on page load
            async function loadApiValues() {
                try {
                    const response = await fetch('/api/values');
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('apiId').value = data.api_id || '';
                        document.getElementById('apiHash').value = data.api_hash || '';
                    }
                } catch (error) {
                    console.error('Failed to load API values:', error);
                }
            }
            
            loadApiValues();
            
            // Form handling
            const sendOtpBtn = document.getElementById('sendOtpBtn');
            const verifyOtpBtn = document.getElementById('verifyOtpBtn');
            const verifyPasswordBtn = document.getElementById('verifyPasswordBtn');
            const updateApiBtn = document.getElementById('updateApiBtn');
            const messageArea = document.getElementById('messageArea');
            const apiResponseArea = document.getElementById('apiResponseArea');
            
            function showMessage(message, type = 'success') {
                messageArea.innerHTML = `<div class="${type}-message">${message}</div>`;
                setTimeout(() => {
                    messageArea.innerHTML = '';
                }, 5000);
            }
            
            function showLoading(button) {
                button.innerHTML = '<span class="loading"></span>Processing...';
                button.disabled = true;
            }
            
            function hideLoading(button, text) {
                button.innerHTML = text;
                button.disabled = false;
            }
            
            sendOtpBtn.addEventListener('click', async () => {
                const phone = document.getElementById('phone').value;
                if (!phone) {
                    showMessage('Please enter a valid phone number', 'error');
                    return;
                }
                
                showLoading(sendOtpBtn);
                
                try {
                    const response = await fetch('/send-otp', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `phone=${encodeURIComponent(phone)}`
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showMessage('OTP sent successfully!', 'success');
                        document.getElementById('phoneButtonGroup').classList.add('hidden');
                        document.getElementById('otpGroup').classList.remove('hidden');
                        document.getElementById('otpButtonGroup').classList.remove('hidden');
                    } else {
                        showMessage(result.detail || 'Error sending OTP', 'error');
                        hideLoading(sendOtpBtn, 'Send OTP');
                    }
                } catch (error) {
                    showMessage('Network error occurred', 'error');
                    hideLoading(sendOtpBtn, 'Send OTP');
                }
            });
            
            verifyOtpBtn.addEventListener('click', async () => {
                const otp = document.getElementById('otp').value;
                if (!otp) {
                    showMessage('Please enter the OTP', 'error');
                    return;
                }
                
                showLoading(verifyOtpBtn);
                
                try {
                    const response = await fetch('/verify-otp', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `otp=${encodeURIComponent(otp)}`
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        if (result.needs_password) {
                            showMessage('2FA detected. Please enter your password.', 'success');
                            document.getElementById('otpButtonGroup').classList.add('hidden');
                            document.getElementById('passwordGroup').classList.remove('hidden');
                            document.getElementById('passwordButtonGroup').classList.remove('hidden');
                        } else {
                            showMessage('Session created successfully! File: userbot_session.session', 'success');
                        }
                    } else {
                        showMessage(result.detail || 'Invalid OTP', 'error');
                        hideLoading(verifyOtpBtn, 'Verify');
                    }
                } catch (error) {
                    showMessage('Network error occurred', 'error');
                    hideLoading(verifyOtpBtn, 'Verify');
                }
            });
            
            verifyPasswordBtn.addEventListener('click', async () => {
                const password = document.getElementById('password').value;
                if (!password) {
                    showMessage('Please enter your 2FA password', 'error');
                    return;
                }
                
                showLoading(verifyPasswordBtn);
                
                try {
                    const response = await fetch('/verify-password', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: `password=${encodeURIComponent(password)}`
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showMessage('Session created successfully! File: userbot_session.session', 'success');
                    } else {
                        showMessage(result.detail || 'Invalid password', 'error');
                        hideLoading(verifyPasswordBtn, 'Verify Password');
                    }
                } catch (error) {
                    showMessage('Network error occurred', 'error');
                    hideLoading(verifyPasswordBtn, 'Verify Password');
                }
            });
            
            // API Update Handler
            updateApiBtn.addEventListener('click', async () => {
                const apiId = document.getElementById('apiId').value;
                const apiHash = document.getElementById('apiHash').value;
                
                if (!apiId || !apiHash) {
                    apiResponseArea.innerHTML = '<div class="error-message">Please enter both API ID and API Hash</div>';
                    setTimeout(() => {
                        apiResponseArea.innerHTML = '';
                    }, 5000);
                    return;
                }
                
                showLoading(updateApiBtn);
                
                try {
                    const response = await fetch(`/updateapi?apiid=${encodeURIComponent(apiId)}&apihash=${encodeURIComponent(apiHash)}`);
                    const result = await response.json();
                    
                    if (response.ok) {
                        apiResponseArea.innerHTML = `<div class="response-box">${JSON.stringify(result, null, 2)}</div>`;
                    } else {
                        apiResponseArea.innerHTML = `<div class="error-message">Failed to update API values</div>`;
                        setTimeout(() => {
                            apiResponseArea.innerHTML = '';
                        }, 5000);
                    }
                    
                    hideLoading(updateApiBtn, 'Update');
                } catch (error) {
                    apiResponseArea.innerHTML = '<div class="error-message">Network error occurred</div>';
                    setTimeout(() => {
                        apiResponseArea.innerHTML = '';
                    }, 5000);
                    hideLoading(updateApiBtn, 'Update');
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/send-otp")
async def send_otp(phone: str = Form(...)):
    global current_client, current_phone, phone_code_hash
    
    try:
        current_client = TelegramClient('userbot_session', API_ID, API_HASH)
        await current_client.connect()

        result = await current_client.send_code_request(phone)
        current_phone = phone
        phone_code_hash = result.phone_code_hash
        
        return JSONResponse({"success": True, "message": "OTP sent successfully"})
        
    except Exception as e:
        if current_client:
            await current_client.disconnect()
        raise HTTPException(status_code=400, detail=f"Failed to send OTP: {str(e)}")

@app.post("/verify-otp")
async def verify_otp(otp: str = Form(...)):
    global current_client, current_phone, phone_code_hash
    
    if not current_client or not current_phone or not phone_code_hash:
        raise HTTPException(status_code=400, detail="Please send OTP first")
    
    try:
        await current_client.sign_in(current_phone, otp, phone_code_hash=phone_code_hash)

        await current_client.disconnect()

        try:
            result = subprocess.run(['supervisorctl', 'restart', PROCESS_NAME], 
                                  capture_output=True, text=True, check=True)
            restart_message = "Service restarted successfully"
        except subprocess.CalledProcessError as e:
            restart_message = f"Service restart failed: {e.stderr}"
        except FileNotFoundError:
            restart_message = "supervisorctl not found in system"
        
        return JSONResponse({
            "success": True, 
            "message": f"Authentication successful. {restart_message}",
            "needs_password": False
        })
        
    except SessionPasswordNeededError:
        return JSONResponse({
            "success": True,
            "message": "2FA detected",
            "needs_password": True
        })
        
    except PhoneCodeInvalidError:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    except Exception as e:
        if current_client:
            await current_client.disconnect()
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")

@app.post("/verify-password")
async def verify_password(password: str = Form(...)):
    global current_client
    
    if not current_client:
        raise HTTPException(status_code=400, detail="Please complete OTP verification first")
    
    try:
        await current_client.sign_in(password=password)

        await current_client.disconnect()

        try:
            result = subprocess.run(['supervisorctl', 'restart', PROCESS_NAME], 
                                  capture_output=True, text=True, check=True)
            restart_message = "Service restarted successfully"
        except subprocess.CalledProcessError as e:
            restart_message = f"Service restart failed: {e.stderr}"
        except FileNotFoundError:
            restart_message = "supervisorctl not found in system"
        
        return JSONResponse({
            "success": True,
            "message": f"Authentication successful with 2FA."
        })
        
    except PasswordHashInvalidError:
        raise HTTPException(status_code=400, detail="Invalid 2FA password")
        
    except Exception as e:
        if current_client:
            await current_client.disconnect()
        raise HTTPException(status_code=400, detail=f"Password verification failed: {str(e)}")
        
@app.get("/updateapi")
async def update_api(apiid: str = Query(...), apihash: str = Query(...)):
    file_path = os.path.join(os.path.dirname(__file__), "values.json")

    data = {
        "api_id": apiid,
        "api_hash": apihash
    }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    try:
        subprocess.run(["supervisorctl", "restart", PROCESS_NAME], check=True)
        restart_status = "Supervisor restarted successfully"
    except subprocess.CalledProcessError as e:
        restart_status = f"Failed to restart: {e}"
    except FileNotFoundError:
        restart_status = "supervisorctl not found in system"

    return {
        "status": "success",
        "updated_values": data,
        "restart": restart_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)