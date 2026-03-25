import { LayoutDashboard, ExternalLink } from "lucide-react";
export default function ChromeExtensionView() {

    return (
        <div className="chrome-extension-view">
            <div style={{
                width: 306,
                height: 650,
                backgroundColor: "#080d18",
                color: "#e8eaed",
                padding: "0px 14px",
                borderRadius: "0px",
                overflow: "hidden",
                margin: "0",

            }}>
                <div className="div-top-bar">
                    <div style={{
                        width: "100%",
                        height: 43,
                        backgroundColor: "#060b15",
                        padding: "0 px",
                        boxSizing: "border-box",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        borderBottomStyle: "solid",
                        borderBottomWidth: "1px",
                        borderBottomColor: "rgb(26,37,64)"

                    }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="#06B6D4">
                                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                            </svg>
                            <span style={{
                                fontFamily: "IBM Plex Mono, monospace",
                                fontSize: "12px",
                                fontWeight: 700,
                                letterSpacing: "0.06em",
                                color: "#06B6D4"
                            }}>
                                ADAPTIVESEC
                            </span>
                        </div>
                        <span style={{
                            fontFamily: "IBM Plex Mono, monospace",
                            fontSize: "10px",
                            color: "#22c55e"
                        }}>
                            ● MONITORING
                        </span>
                    </div>
                </div>
                <div className="div-jit-nudge" style={{ padding: "14px" }}>
                    <div style={{
                        height: "135px",
                        background: "linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(239, 68, 68, 0.08))",
                        border: "1px solid #f97316",
                        borderColor: "rgba(245,158,11, 0.3)",
                        borderRadius: "8px",
                        padding: "10px 12px",
                        boxSizing: "border-box",
                        overflow: "hidden",
                    }}>
                        <div className="jit-title">
                            <span>⚠️</span>
                            <span style={{
                                fontFamily: "IBM Plex Mono, monospace",
                                fontSize: "10px",
                                fontWeight: 600,
                                color: "#f59e0b",
                            }}>
                                Just-In-Time Training Nudge
                            </span>
                            <p style={{
                                fontSize: "10px",
                                color: "white",
                                lineHeight: "1.5",
                                marginBottom: "4px",
                                fontFamily: "IBM Plex Sans, sans-serif",

                            }}>
                                You just clicked a link from an unverified domain. This matches a pattern linked to your risk profile.
                            </p>
                            <div className="jit-class-trigger" style={{ height: "26.23px" }}>
                                <span style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    height: "18px",
                                    width: "144px",
                                    backgroundColor: "#f59e0b26",
                                    borderRadius: "4px",
                                }}>
                                    <span style={{
                                        fontSize: "10px",
                                        display: "inline-block",
                                        color: "#f59e0b",
                                        fontFamily: "IBM Plex Mono, monospace",
                                        padding: "2px 7px",
                                    }}>
                                        ⚡ Urgency Bias Trigger
                                    </span>
                                </span>
                            </div>
                            <div className="jit-btn" style={{
                                height: "22px",
                                display: "flex",
                                gap: "8px",
                                alignItems: "center",
                            }}>
                                <button style={{
                                    backgroundColor: "#f59e0b",
                                    borderRadius: "5px",
                                    boxSizing: "border-box",
                                    width: "212px",
                                    padding: "6px 10px",
                                    height: "28px",
                                    border: "none",

                                }}>
                                    <span style={{
                                        fontSize: "11px",
                                        fontWeight: 600,
                                        color: "#000",
                                        cursor: "pointer",
                                        fontFamily: "'IBM Plex Sans', sans-serif",
                                        textAlign: "center",

                                    }}>
                                        Watch 30s Lesson ▶
                                    </span>
                                </button>
                                <button style={{
                                    backgroundColor: "#67848B",
                                    padding: "6px 10px",
                                    border: "1px solid #243050",
                                    borderRadius: "5px",
                                    fontSize: "11px",
                                    cursor: "pointer",
                                    fontFamily: "'IBM Plex Sans', sans-serif",
                                    background: "transparent",
                                    color: "67848B",
                                }}>
                                    <span style={{
                                        color: "#67848B",
                                    }}>
                                        Dismiss
                                    </span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="popup-score" style={{
                    height: "72px",
                    display: "flex",
                    alignItems: "center",
                    gap: "14px",
                    marginBottom: "14px",
                    marginLeft: "14px",
                }}>
                    {/* Risk Score */}
                    <div style={{
                        width: "56px",
                        height: "56px",
                        borderRadius: "50%",
                        border: "5px solid #F97316",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                    }}>
                        <span style={{
                            fontSize: "20px",
                            fontWeight: "600",
                            color: "#F97316",
                            lineHeight: 1,
                            fontFamily: "IBM Plex Mono, monospace",
                        }}>
                            58
                        </span>
                        <span style={{
                            fontSize: "9px",
                            color: "#64748b",
                            letterSpacing: "0.1em",
                            marginTop: "2px",
                            fontFamily: "IBM Plex Mono, monospace",

                        }}>
                            RISK
                        </span>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        <span style={{
                            fontSize: "14px",
                            fontWeight: "600",
                            color: "#f97316",
                            marginBottom: "3px",
                            fontFamily: "IBM Plex Mono, monospace",
                        }}>
                            High Risk
                        </span>
                        <span style={{
                            fontSize: "11px",
                            color: "#10b981",
                            fontFamily: "IBM Plex Mono, monospace",
                            marginTop: "-6px",


                        }}>
                            ↘ -8 pts this week
                        </span>
                        <span style={{
                            fontSize: "10px",
                            color: "#64748b",
                            fontFamily: "IBM Plex Mono, monospace",

                        }}>
                            Updated 5 min ago
                        </span>
                    </div>
                </div>
                <div className="vuln-profile" style={{
                    height: "47px",
                    backgroundColor: "#8b5cf61a",
                    border: "1px solid #8b5cf61a",
                    borderRadius: "8px",
                    marginBottom: "14px",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                }}>
                    <span style={{ fontSize: "16px", marginLeft: "8px" }}>🧠</span>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                        <span style={{
                            fontSize: "11px",
                            fontFamily: "IBM Plex Mono, monospace",
                            color: "#64748b",
                            letterSpacing: "0.1em",
                        }}>
                            VULNERABILITY PROFILE
                        </span>
                        <span style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            color: "#a78bfa",
                            fontFamily: "IBM Plex Mono, monospace",
                        }}>
                            High Urgency Susceptibility
                        </span>
                    </div>
                </div>
                <div className="trend-chart" style={{
                    height: "66px",
                }}>
                    <div className="trend-chart-header" style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "6px",
                        color: "#E2E8F0",
                        height: "12.5px",
                    }}>
                        <span style={{
                            fontSize: "11px",
                            color: "#64748b",
                            fontFamily: "IBM Plex Mono, monospace",
                            letterSpacing: "0.1em",
                        }}>
                            30-DAY TREND
                        </span>
                        <span style={{
                            fontSize: "11px",
                            color: "#3b82f6",
                            cursor: "pointer",
                            fontFamily: "IBM Plex Mono, monospace",
                        }}>
                            Full View →
                        </span>
                    </div>
                    <svg width="100%" height="40" viewBox="0 0 308 40" fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        style={{ overflow: "visible" }}
                    >
                        <defs>
                            <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#f97316" stopOpacity="0.4" />
                                <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
                            </linearGradient>
                        </defs>

                        {/* shadow fill */}
                        <path
                            d="M 0 20 C 30 18 50 28 80 24 C 110 20 130 10 160 14 C 190 18 220 30 260 26 C 280 24 295 20 308 22 L 308 40 L 0 40 Z"
                            fill="url(#sparkGradient)"
                        />

                        {/* line */}
                        <path
                            d="M 0 20 C 30 18 50 28 80 24 C 110 20 130 10 160 14 C 190 18 220 30 260 26 C 280 24 295 20 308 22"
                            fill="none"
                            stroke="rgb(249, 115, 22)"
                            strokeWidth="1.5"
                        />

                        {/* dot */}
                        <circle cx="308" cy="22" r="4" fill="#f97316" />
                    </svg>
                </div>
                <div className="assigned-training-header" style={{
                    height: "12.5px",
                }}>
                    <span style={{
                        fontSize: "11px",
                        fontFamily: "IBM Plex Mono, monospace",
                        color: "#64748b",
                        letterSpacing: "0.1em",

                    }}>
                        ASSIGNED TRAINING
                    </span>
                </div>
                <div className="assigned-training-content" style={{
                    height: "auto",
                    display: "flex",
                    gap: "8px",
                    marginTop: "10px",
                    flexDirection: "column",
                }}>
                    {/* Phishing Awareness Training */}
                    <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                    }}>
                        <span style={{
                            width: "28px",
                            height: "28px",
                            borderRadius: "6px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor: "rgba(59, 130, 246, 0.15)",
                            border: "1px solid rgba(59, 130, 246, 0.3)",
                            flexShrink: 0,
                        }}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polygon points="10 8 16 12 10 16 10 8"></polygon>
                            </svg>
                        </span>
                        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: "12px", color: "#E2E8F0", fontWeight: "600", fontFamily: "IBM Plex Mono, monospace" }}>Phishing Awareness</span>
                                <span style={{ fontSize: "11px", color: "#3b82f6", fontFamily: "IBM Plex Mono, monospace" }}>75%</span>
                            </div>
                            <div style={{ height: "3px", backgroundColor: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                                <div style={{ width: "75%", height: "100%", backgroundColor: "#3b82f6", borderRadius: "2px" }} />
                            </div>
                        </div>
                    </div>
                    {/* Password Security Training */}
                    <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        marginTop: "10px",
                    }}>
                        <span style={{
                            width: "28px",
                            height: "28px",
                            borderRadius: "6px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor: "rgba(34, 197, 94, 0.15)",
                            border: "1px solid rgba(34, 197, 94, 0.3)",
                            flexShrink: 0,
                        }}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                        </span>
                        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: "12px", color: "#E2E8F0", fontWeight: "600", fontFamily: "IBM Plex Mono, monospace" }}>Password Security ✓</span>
                                <span style={{ fontSize: "11px", color: "#22c55e", fontFamily: "IBM Plex Mono, monospace" }}>100%</span>
                            </div>
                            <div style={{ height: "3px", backgroundColor: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                                <div style={{ width: "100%", height: "100%", backgroundColor: "#22c55e", borderRadius: "2px" }} />
                            </div>
                        </div>
                    </div>

                    {/* Social Engineering Training */}
                    <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        marginTop: "10px",
                        paddingBottom: "10px",
                        borderBottomStyle: "solid",
                        borderBottomWidth: "1px",
                        borderBottomColor: "rgb(26,37,64)",
                    }}>
                        <span style={{
                            width: "28px",
                            height: "28px",
                            borderRadius: "6px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor: "rgba(249, 115, 22, 0.15)",
                            border: "1px solid rgba(249, 115, 22, 0.3)",
                            flexShrink: 0,
                        }}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f97316" strokeWidth="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </span>
                        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ fontSize: "12px", color: "#E2E8F0", fontWeight: "600", fontFamily: "IBM Plex Mono, monospace" }}>Social Engineering</span>
                                <span style={{ fontSize: "11px", color: "#f97316", fontFamily: "IBM Plex Mono, monospace" }}>30%</span>
                            </div>
                            <div style={{ height: "3px", backgroundColor: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                                <div style={{ width: "30%", height: "100%", backgroundColor: "#f97316", borderRadius: "2px" }} />
                            </div>

                        </div>
                    </div>
                    <div className="dashboard-button" style={{
                        height: "35px",
                        width: "100%",
                        background: "linear-gradient(135deg, #1d4ed8, #06b6d4)",
                        borderRadius: "8px",
                        border: "none",
                        fontSize: "14px",
                        fontWeight: "700",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "8px",
                        fontFamily: "IBM Plex Mono, monospace",
                        color: "#fff",
                        marginTop: "10px",
                    }}>
                        <LayoutDashboard size={14} color="#fff" />
                        Open Full Dashboard
                        <ExternalLink size={14} color="#fff" />
                    </div>
                </div>
            </div >
        </div >
    )
}