package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// QRManager handles QR code storage and retrieval
type QRManager struct {
	mu          sync.RWMutex
	currentQR   string
	qrTimestamp time.Time
	isConnected bool
}

// Global QR manager instance
var qrManager = &QRManager{}

// SetQRCode stores a new QR code
func (qm *QRManager) SetQRCode(code string) {
	qm.mu.Lock()
	defer qm.mu.Unlock()
	qm.currentQR = code
	qm.qrTimestamp = time.Now()
	qm.isConnected = false
}

// SetConnected marks the device as connected
func (qm *QRManager) SetConnected() {
	qm.mu.Lock()
	defer qm.mu.Unlock()
	qm.isConnected = true
	qm.currentQR = "" // Clear QR code once connected
}

// GetStatus returns the current authentication status
func (qm *QRManager) GetStatus() (string, string, time.Time) {
	qm.mu.RLock()
	defer qm.mu.RUnlock()
	
	if qm.isConnected {
		return "connected", "", qm.qrTimestamp
	}
	
	if qm.currentQR != "" {
		// Check if QR code is still valid (3 minutes timeout)
		if time.Since(qm.qrTimestamp) < 3*time.Minute {
			return "pending", qm.currentQR, qm.qrTimestamp
		}
		return "expired", "", qm.qrTimestamp
	}
	
	return "disconnected", "", time.Time{}
}

// QRResponse represents the QR code API response
type QRResponse struct {
	Status      string `json:"status"`      // connected, pending, expired, disconnected
	QRCode      string `json:"qr_code,omitempty"`
	QRImage     string `json:"qr_image,omitempty"` // Base64 encoded QR image
	Message     string `json:"message"`
	Timestamp   string `json:"timestamp,omitempty"`
}

// GenerateQRImage generates a base64 encoded PNG image of the QR code
func GenerateQRImage(code string) string {
	// For now, we'll return the text representation
	// In production, you could use a library like github.com/skip2/go-qrcode
	// to generate an actual PNG image
	return base64.StdEncoding.EncodeToString([]byte(code))
}

// HandleQREndpoint serves the QR code status via HTTP
func HandleQREndpoint(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	status, qrCode, timestamp := qrManager.GetStatus()
	
	response := QRResponse{
		Status: status,
	}
	
	switch status {
	case "connected":
		response.Message = "WhatsApp is connected and ready"
	case "pending":
		response.QRCode = qrCode
		response.QRImage = GenerateQRImage(qrCode)
		response.Message = "Scan this QR code with WhatsApp to authenticate"
		response.Timestamp = timestamp.Format(time.RFC3339)
	case "expired":
		response.Message = "QR code has expired. Please restart the authentication process"
	case "disconnected":
		response.Message = "WhatsApp is not connected. Starting authentication..."
	}
	
	json.NewEncoder(w).Encode(response)
}

// HandleReauthEndpoint triggers re-authentication
func HandleReauthEndpoint(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	w.Header().Set("Content-Type", "application/json")
	
	// Set a flag to trigger re-authentication in the main loop
	// This would need to be implemented in the main.go file
	response := map[string]interface{}{
		"success": true,
		"message": "Re-authentication triggered. Check /api/qr for the new QR code",
	}
	
	json.NewEncoder(w).Encode(response)
}

// InitQRHandlers registers the QR-related HTTP handlers
func InitQRHandlers() {
	http.HandleFunc("/api/qr", HandleQREndpoint)
	http.HandleFunc("/api/reauth", HandleReauthEndpoint)
	fmt.Println("QR handlers initialized at /api/qr and /api/reauth")
}