"""
MCP Server for Slotix.

This server provides tools for managing appointments, clients, and notifications
through AI assistants like Claude Desktop and ChatGPT.
"""
import asyncio
import json
from datetime import datetime, date
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import SlotixClient
from . import __version__


# Initialize MCP server
server = Server("slotix")
client: SlotixClient | None = None


def get_client() -> SlotixClient:
    """Get or create the Slotix client."""
    global client
    if client is None:
        client = SlotixClient()
    return client


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt_str


def format_date(d_str: str) -> str:
    """Format date string for display."""
    try:
        d = date.fromisoformat(d_str)
        return d.strftime("%d/%m/%Y")
    except Exception:
        return d_str


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_profile",
            description="Get your professional profile with all business details. Returns: name, email, phone, business info (name, address, city, postal code, country, VAT, website), localization (timezone, currency, language), booking settings (slot duration, notice hours, max days ahead, client modification rules, reminder times), enabled features (Telegram, WhatsApp, catalog, reminders, feedback, coupons, AI), coupon settings, and AI custom prompt.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_appointments",
            description="Get appointments within a date range. Default: next 7 days. Use filters for specific dates or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD). Default: today"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Default: start_date + 7 days"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: booked, completed, cancelled, no_show",
                        "enum": ["booked", "completed", "cancelled", "no_show"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_today_appointments",
            description="Get all appointments scheduled for today.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_week_appointments",
            description="Get all appointments for the current week (Monday to Sunday).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_appointment",
            description="Get full details of a specific appointment. Returns: client info (name, contact, ID), date/time, duration, status, source, notes, services, payment info (total price, amount paid, method, notes, complete status), feedback (rating, comment, sentiment), and timestamps (created_at, updated_at).",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID"
                    }
                },
                "required": ["appointment_id"]
            }
        ),
        Tool(
            name="create_appointment",
            description="Create a new appointment for a client. Either client_name or client_id must be provided. If client_id is provided, client info is resolved from the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "Client's name (optional if client_id is provided)"
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "Appointment date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Always use the current year."
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration in minutes (default: 30)",
                        "default": 30
                    },
                    "client_contact": {
                        "type": "string",
                        "description": "Client's contact (email or phone)"
                    },
                    "client_id": {
                        "type": "integer",
                        "description": "Existing client ID. If provided, client_name and client_contact are resolved from DB."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes for the appointment"
                    }
                },
                "required": ["start_datetime"]
            }
        ),
        Tool(
            name="update_appointment",
            description="Update an existing appointment (reschedule, add notes, change status, update payment). Returns updated appointment with all fields including timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID to update"
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "New date and time (ISO 8601 format)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "New duration in minutes"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status: booked, completed, cancelled, no_show",
                        "enum": ["booked", "completed", "cancelled", "no_show"]
                    },
                    "amount_paid": {
                        "type": "number",
                        "description": "Amount paid by the client"
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method: cash, card, transfer, etc."
                    },
                    "payment_notes": {
                        "type": "string",
                        "description": "Payment notes (e.g., 'Paid 50%, rest next visit')"
                    },
                    "payment_complete": {
                        "type": "boolean",
                        "description": "Whether the payment is complete"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Updated notes"
                    }
                },
                "required": ["appointment_id"]
            }
        ),
        Tool(
            name="cancel_appointment",
            description="Cancel an appointment. The appointment will be marked as cancelled (not deleted).",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID to cancel"
                    }
                },
                "required": ["appointment_id"]
            }
        ),
        Tool(
            name="reschedule_appointment",
            description="Reschedule an appointment to a new date/time and optionally notify the client.",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID to reschedule"
                    },
                    "new_datetime": {
                        "type": "string",
                        "description": "New date and time (ISO 8601 format)"
                    },
                    "notify_client": {
                        "type": "boolean",
                        "description": "Send notification to client about the change",
                        "default": True
                    },
                    "message": {
                        "type": "string",
                        "description": "Custom message to send to client (optional)"
                    }
                },
                "required": ["appointment_id", "new_datetime"]
            }
        ),
        Tool(
            name="get_clients",
            description="Get list of clients. Optionally search by name, email, or phone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term (name, email, or phone)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of clients to return (default: 50)",
                        "default": 50
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_client",
            description="Get detailed information about a specific client including appointment history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "The client ID"
                    }
                },
                "required": ["client_id"]
            }
        ),
        Tool(
            name="get_availability",
            description="Get schedule overview showing all time slots with their status. Available slots are marked as free, occupied slots show the appointment ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD). Default: today"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD). Default: start_date + 7 days"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_stats",
            description="Get business statistics (appointments, revenue, clients) for a time period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period: today, week, month, year",
                        "enum": ["today", "week", "month", "year"],
                        "default": "month"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="send_notification",
            description="Send a message to a client via Telegram or WhatsApp.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "The client ID to send the message to"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Communication channel: telegram, whatsapp, or auto (tries both)",
                        "enum": ["telegram", "whatsapp", "auto"],
                        "default": "auto"
                    }
                },
                "required": ["client_id", "message"]
            }
        ),
        Tool(
            name="create_coupon",
            description="Create and send a discount coupon to a client. The coupon is automatically sent via Telegram or WhatsApp with a QR code. Uses your default settings if discount parameters are not specified.",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "The client ID to send the coupon to"
                    },
                    "discount_type": {
                        "type": "string",
                        "description": "Type of discount: 'fixed' for amount off, 'percentage' for percent off",
                        "enum": ["fixed", "percentage"]
                    },
                    "discount_value": {
                        "type": "number",
                        "description": "Discount amount (for fixed) or percentage (for percentage type)"
                    },
                    "validity_days": {
                        "type": "integer",
                        "description": "Number of days until the coupon expires"
                    }
                },
                "required": ["client_id"]
            }
        ),
        # Catalog (Services/Products)
        Tool(
            name="get_catalog_items",
            description="Get your catalog of services and products. Filter by active status, type (service/product), or category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "is_active": {
                        "type": "boolean",
                        "description": "Filter by active status (true/false)"
                    },
                    "is_product": {
                        "type": "boolean",
                        "description": "Filter by type: true=products, false=services"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category name"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_catalog_item",
            description="Create a new service or product in your catalog.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Item name"
                    },
                    "price": {
                        "type": "number",
                        "description": "Price"
                    },
                    "description": {
                        "type": "string",
                        "description": "Item description"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration in minutes (for services)"
                    },
                    "is_product": {
                        "type": "boolean",
                        "description": "True for product, false for service (default: false)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name"
                    }
                },
                "required": ["name", "price"]
            }
        ),
        Tool(
            name="update_catalog_item",
            description="Update an existing catalog item (service or product).",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "The catalog item ID to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "New item name"
                    },
                    "price": {
                        "type": "number",
                        "description": "New price"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "New duration in minutes"
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Active status"
                    },
                    "is_product": {
                        "type": "boolean",
                        "description": "True for product, false for service"
                    },
                    "category": {
                        "type": "string",
                        "description": "New category name"
                    }
                },
                "required": ["item_id"]
            }
        ),
        Tool(
            name="delete_catalog_item",
            description="Delete a catalog item (service or product).",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "integer",
                        "description": "The catalog item ID to delete"
                    }
                },
                "required": ["item_id"]
            }
        ),
        # Appointment Services
        Tool(
            name="get_appointment_services",
            description="Get all services/products attached to a specific appointment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID"
                    }
                },
                "required": ["appointment_id"]
            }
        ),
        Tool(
            name="add_service_to_appointment",
            description="Add a service or product from your catalog to an appointment. This will update the appointment's total price.",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID"
                    },
                    "catalog_item_id": {
                        "type": "integer",
                        "description": "The catalog item ID to add"
                    }
                },
                "required": ["appointment_id", "catalog_item_id"]
            }
        ),
        Tool(
            name="remove_service_from_appointment",
            description="Remove a service or product from an appointment. This will update the appointment's total price.",
            inputSchema={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The appointment ID"
                    },
                    "service_id": {
                        "type": "integer",
                        "description": "The appointment service record ID (not the catalog item ID)"
                    }
                },
                "required": ["appointment_id", "service_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        slotix = get_client()
        result: Any = None

        if name == "get_profile":
            result = await slotix.get_profile()

            # Build address
            address_parts = []
            if result.get('business_address'):
                address_parts.append(result['business_address'])
            if result.get('business_postal_code') or result.get('business_city'):
                city_line = f"{result.get('business_postal_code', '')} {result.get('business_city', '')}".strip()
                if city_line:
                    address_parts.append(city_line)
            if result.get('business_country'):
                address_parts.append(result['business_country'])
            address = ", ".join(address_parts) if address_parts else "N/A"

            # Build features list
            features = []
            if result.get('telegram_bot_active'):
                features.append("Telegram")
            if result.get('whatsapp_active'):
                features.append("WhatsApp")
            if result.get('catalog_enabled'):
                features.append("Catalog")
            if result.get('reminder_enabled'):
                features.append("Reminders")
            if result.get('feedback_enabled'):
                features.append("Feedback")
            if result.get('coupon_enabled'):
                features.append("Coupons")
            if result.get('ai_enabled'):
                features.append("AI")
            features_str = ", ".join(features) if features else "None"

            # Coupon settings
            coupon_info = ""
            if result.get('coupon_enabled'):
                coupon_info = f"""
**Coupon Settings**
- Spending threshold: {result.get('coupon_spending_threshold', 'N/A')} {result.get('currency', '')}
- Discount: {result.get('coupon_discount_value', 'N/A')} {'%' if result.get('coupon_discount_type') == 'percentage' else result.get('currency', '')}
- Validity: {result.get('coupon_validity_days', 'N/A')} days"""

            # AI prompt
            ai_info = ""
            if result.get('ai_custom_prompt'):
                ai_info = f"""
**AI Configuration**
- Custom prompt: {result.get('ai_custom_prompt')[:200]}{'...' if len(result.get('ai_custom_prompt', '')) > 200 else ''}"""

            text = f"""**SlotixMCP v{__version__}**

**Profile**
- Name: {result.get('full_name', 'N/A')}
- Email: {result.get('email', 'N/A')}
- Phone: {result.get('phone', 'N/A')}

**Business**
- Business name: {result.get('business_name', 'N/A')}
- Address: {address}
- VAT: {result.get('vat_number', 'N/A')}
- Website: {result.get('business_website', 'N/A')}

**Settings**
- Timezone: {result.get('timezone', 'N/A')}
- Currency: {result.get('currency', 'N/A')}
- Language: {result.get('language', 'N/A')}

**Booking**
- Default slot duration: {result.get('default_slot_duration', 30)} minutes
- Minimum notice: {result.get('booking_notice_hours', 24)} hours
- Max days ahead: {result.get('max_booking_days_ahead', 30)} days
- Client can modify: {'Yes' if result.get('allow_client_modifications') else 'No'} (min {result.get('min_hours_before_modification', 24)}h before)
- Reminder times: {result.get('reminder_times', [24])} hours before

**Features Enabled**
{features_str}{coupon_info}{ai_info}"""

        elif name == "get_appointments":
            result = await slotix.get_appointments(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                status=arguments.get("status")
            )
            appointments = result.get("appointments", [])
            if not appointments:
                text = f"No appointments found for {result.get('date_range', 'the selected period')}."
            else:
                text = f"**Appointments** ({result.get('date_range', '')})\n\n"
                for apt in appointments:
                    text += f"- [ID:{apt['id']}] **{apt['client_name']}** - {format_datetime(apt['start_datetime'])} ({apt['duration_minutes']}min) - {apt['status']}"
                    service_ids = apt.get('service_ids', [])
                    if service_ids:
                        text += f" | Service IDs: {service_ids}"
                    if apt.get('created_at'):
                        text += f" | Booked: {format_datetime(apt['created_at'])}"
                    text += "\n"
                    if apt.get('notes'):
                        text += f"  Notes: {apt['notes']}\n"
                text += f"\nTotal: {result.get('total', len(appointments))} appointments"

        elif name == "get_today_appointments":
            result = await slotix.get_today_appointments()
            appointments = result.get("appointments", [])
            if not appointments:
                text = "No appointments scheduled for today."
            else:
                text = "**Today's Appointments**\n\n"
                for apt in appointments:
                    text += f"- [ID:{apt['id']}] **{apt['client_name']}** - {format_datetime(apt['start_datetime'])} ({apt['duration_minutes']}min) - {apt['status']}"
                    service_ids = apt.get('service_ids', [])
                    if service_ids:
                        text += f" | Service IDs: {service_ids}"
                    if apt.get('created_at'):
                        text += f" | Booked: {format_datetime(apt['created_at'])}"
                    text += "\n"
                text += f"\nTotal: {len(appointments)} appointments"

        elif name == "get_week_appointments":
            result = await slotix.get_week_appointments()
            appointments = result.get("appointments", [])
            if not appointments:
                text = "No appointments scheduled for this week."
            else:
                text = f"**This Week's Appointments** ({result.get('date_range', '')})\n\n"
                for apt in appointments:
                    text += f"- [ID:{apt['id']}] **{apt['client_name']}** - {format_datetime(apt['start_datetime'])} ({apt['duration_minutes']}min) - {apt['status']}"
                    service_ids = apt.get('service_ids', [])
                    if service_ids:
                        text += f" | Service IDs: {service_ids}"
                    if apt.get('created_at'):
                        text += f" | Booked: {format_datetime(apt['created_at'])}"
                    text += "\n"
                text += f"\nTotal: {len(appointments)} appointments"

        elif name == "get_appointment":
            result = await slotix.get_appointment(arguments["appointment_id"])
            service_ids = result.get('service_ids', [])
            services_line = f"\n- Service IDs: {service_ids}" if service_ids else ""

            # Build payment info
            payment_info = ""
            if result.get('total_price') or result.get('amount_paid'):
                payment_info = f"""
- Total Price: {result.get('total_price', 'N/A')}
- Amount Paid: {result.get('amount_paid', '0')}
- Payment Method: {result.get('payment_method', 'N/A')}
- Payment Notes: {result.get('payment_notes', 'None')}
- Payment Complete: {'Yes' if result.get('payment_complete') else 'No'}"""

            # Build feedback info
            feedback_info = ""
            if result.get('feedback_rating'):
                feedback_info = f"""
- Feedback Rating: {result.get('feedback_rating')}/5
- Feedback Comment: {result.get('feedback_comment', 'None')}
- Feedback Sentiment: {result.get('feedback_sentiment', 'N/A')}"""

            # Build timestamps
            created = format_datetime(result['created_at']) if result.get('created_at') else 'N/A'
            updated = format_datetime(result['updated_at']) if result.get('updated_at') else 'N/A'

            text = f"""**Appointment #{result['id']}**
- Client: {result['client_name']}
- Contact: {result.get('client_contact', 'N/A')}
- Client ID: {result.get('client_id', 'N/A')}
- Date: {format_datetime(result['start_datetime'])} - {format_datetime(result['end_datetime'])}
- Duration: {result['duration_minutes']} minutes
- Status: {result['status']}
- Source: {result['source']}
- Notes: {result.get('notes', 'None')}{services_line}{payment_info}{feedback_info}
- Created: {created}
- Updated: {updated}"""

        elif name == "create_appointment":
            result = await slotix.create_appointment(
                start_datetime=arguments["start_datetime"],
                duration_minutes=arguments.get("duration_minutes", 30),
                client_name=arguments.get("client_name"),
                client_contact=arguments.get("client_contact"),
                client_id=arguments.get("client_id"),
                notes=arguments.get("notes")
            )
            text = f"""**Appointment Created**
- ID: {result['id']}
- Client: {result['client_name']}
- Date: {format_datetime(result['start_datetime'])}
- Duration: {result['duration_minutes']} minutes
- Status: {result['status']}"""

        elif name == "update_appointment":
            result = await slotix.update_appointment(
                appointment_id=arguments["appointment_id"],
                start_datetime=arguments.get("start_datetime"),
                duration_minutes=arguments.get("duration_minutes"),
                status=arguments.get("status"),
                notes=arguments.get("notes"),
                amount_paid=arguments.get("amount_paid"),
                payment_method=arguments.get("payment_method"),
                payment_notes=arguments.get("payment_notes"),
                payment_complete=arguments.get("payment_complete")
            )
            # Build payment info if available
            payment_info = ""
            if result.get('total_price') or result.get('amount_paid'):
                payment_info = f"""
- Total Price: {result.get('total_price', 'N/A')}
- Amount Paid: {result.get('amount_paid', '0')}
- Payment Method: {result.get('payment_method', 'N/A')}
- Payment Notes: {result.get('payment_notes', 'None')}
- Payment Complete: {'Yes' if result.get('payment_complete') else 'No'}"""

            # Build timestamps
            updated = format_datetime(result['updated_at']) if result.get('updated_at') else 'N/A'

            text = f"""**Appointment Updated**
- ID: {result['id']}
- Client: {result['client_name']}
- Date: {format_datetime(result['start_datetime'])}
- Duration: {result['duration_minutes']} minutes
- Status: {result['status']}{payment_info}
- Updated: {updated}"""

        elif name == "cancel_appointment":
            result = await slotix.cancel_appointment(arguments["appointment_id"])
            text = f"**Appointment #{arguments['appointment_id']} cancelled.**"

        elif name == "reschedule_appointment":
            # First update the appointment
            result = await slotix.update_appointment(
                appointment_id=arguments["appointment_id"],
                start_datetime=arguments["new_datetime"]
            )
            text = f"""**Appointment Rescheduled**
- ID: {result['id']}
- Client: {result['client_name']}
- New Date: {format_datetime(result['start_datetime'])}"""

            # Optionally notify the client
            if arguments.get("notify_client", True) and result.get("client_id"):
                # Get user's language for localized message
                profile = await slotix.get_profile()
                lang = profile.get("language", "en")

                # Localized reschedule messages
                reschedule_messages = {
                    "it": f"Il tuo appuntamento è stato spostato a {format_datetime(result['start_datetime'])}.",
                    "en": f"Your appointment has been rescheduled to {format_datetime(result['start_datetime'])}.",
                    "de": f"Ihr Termin wurde auf {format_datetime(result['start_datetime'])} verschoben.",
                    "fr": f"Votre rendez-vous a été déplacé au {format_datetime(result['start_datetime'])}.",
                    "es": f"Su cita ha sido reprogramada para el {format_datetime(result['start_datetime'])}.",
                }
                default_message = reschedule_messages.get(lang, reschedule_messages["en"])
                message = arguments.get("message") or default_message

                try:
                    notify_result = await slotix.send_notification(
                        client_id=result["client_id"],
                        message=message
                    )
                    if notify_result.get("success"):
                        text += f"\n\nClient notified via {notify_result.get('channel_used', 'messaging')}."
                    else:
                        text += f"\n\nNote: Could not notify client - {notify_result.get('message', 'unknown error')}"
                except Exception as e:
                    text += f"\n\nNote: Could not notify client - {str(e)}"

        elif name == "get_clients":
            result = await slotix.get_clients(
                search=arguments.get("search"),
                limit=arguments.get("limit", 50)
            )
            clients = result.get("clients", [])
            if not clients:
                text = "No clients found."
            else:
                text = "**Clients**\n\n"
                for c in clients:
                    text += f"- **{c['full_name']}** (ID: {c['id']})"
                    if c.get('phone'):
                        text += f" - {c['phone']}"
                    if c.get('email'):
                        text += f" - {c['email']}"
                    text += f" - {c['total_appointments']} appointments"
                    if c.get('is_banned'):
                        text += " [BANNED]"
                    text += "\n"
                text += f"\nTotal: {result.get('total', len(clients))} clients"

        elif name == "get_client":
            result = await slotix.get_client(arguments["client_id"])
            text = f"""**Client #{result['id']}**
- Name: {result['full_name']}
- Email: {result.get('email', 'N/A')}
- Phone: {result.get('phone', 'N/A')}
- Telegram: {result.get('telegram_username', 'N/A')}
- Total Appointments: {result['total_appointments']}
- Total Spent: {result['total_spent']}
- Notes: {result.get('notes', 'None')}
- Status: {'BANNED' if result.get('is_banned') else 'Active'}"""

        elif name == "get_availability":
            result = await slotix.get_availability(
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date")
            )
            if not result:
                text = "No slots found for the selected period."
            else:
                text = "**Schedule Overview**\n\n"
                for day in result:
                    text += f"**{format_date(day['date'])}**\n"
                    for slot in day.get("slots", []):
                        time_range = f"{slot['start_time']} - {slot['end_time']}"
                        if slot.get("available", True):
                            text += f"  - {time_range} ✓ Available\n"
                        else:
                            apt_id = slot.get("appointment_id")
                            text += f"  - {time_range} ✗ Occupied [Appointment ID:{apt_id}]\n"
                    text += "\n"

        elif name == "get_stats":
            period = arguments.get("period", "month")
            result = await slotix.get_stats(period=period)
            text = f"""**Statistics ({result.get('period', period).capitalize()})**
- Total Appointments: {result['total_appointments']}
  - Completed: {result['completed_appointments']}
  - Cancelled: {result['cancelled_appointments']}
  - No-shows: {result['no_show_appointments']}
- Total Revenue: {result['total_revenue']}
- Avg. Appointment Value: {result.get('average_appointment_value', 'N/A')}
- Total Clients: {result['total_clients']}
- New Clients: {result['new_clients']}"""

        elif name == "send_notification":
            result = await slotix.send_notification(
                client_id=arguments["client_id"],
                message=arguments["message"],
                channel=arguments.get("channel", "auto")
            )
            if result.get("success"):
                text = f"**Message sent** via {result.get('channel_used', 'messaging')}."
            else:
                text = f"**Failed to send message**: {result.get('message', 'Unknown error')}"

        elif name == "create_coupon":
            result = await slotix.create_coupon(
                client_id=arguments["client_id"],
                discount_type=arguments.get("discount_type"),
                discount_value=arguments.get("discount_value"),
                validity_days=arguments.get("validity_days")
            )
            if result.get("success"):
                expires = result.get("expires_at", "")
                if expires:
                    try:
                        expires = format_datetime(expires)
                    except Exception:
                        pass
                text = f"""**Coupon Created**
- Code: {result.get('coupon_code', 'N/A')}
- Discount: {result.get('discount_display', 'N/A')}
- Expires: {expires or 'N/A'}
- Status: {result.get('message', 'Sent')}"""
            else:
                text = f"**Failed to create coupon**: {result.get('message', 'Unknown error')}"

        # Catalog (Services/Products)
        elif name == "get_catalog_items":
            result = await slotix.get_catalog_items(
                is_active=arguments.get("is_active"),
                is_product=arguments.get("is_product"),
                category=arguments.get("category")
            )
            items = result.get("items", [])
            if not items:
                text = "No catalog items found."
            else:
                text = "**Catalog Items**\n\n"
                for item in items:
                    item_type = "Product" if item.get("is_product") else "Service"
                    status = "Active" if item.get("is_active") else "Inactive"
                    duration = f" ({item['duration_minutes']}min)" if item.get("duration_minutes") else ""
                    text += f"- [ID:{item['id']}] **{item['name']}** - {item['price']}{duration} - {item_type} - {status}\n"
                text += f"\nTotal: {result.get('total', len(items))} items"

        elif name == "create_catalog_item":
            result = await slotix.create_catalog_item(
                name=arguments["name"],
                price=arguments["price"],
                description=arguments.get("description"),
                duration_minutes=arguments.get("duration_minutes"),
                is_active=arguments.get("is_active", True),
                is_product=arguments.get("is_product", False),
                category=arguments.get("category")
            )
            item_type = "Product" if result.get("is_product") else "Service"
            text = f"""**Catalog Item Created**
- ID: {result['id']}
- Name: {result['name']}
- Price: {result['price']}
- Type: {item_type}
- Duration: {result.get('duration_minutes', 'N/A')} minutes
- Category: {result.get('category', 'N/A')}"""

        elif name == "update_catalog_item":
            result = await slotix.update_catalog_item(
                item_id=arguments["item_id"],
                name=arguments.get("name"),
                price=arguments.get("price"),
                description=arguments.get("description"),
                duration_minutes=arguments.get("duration_minutes"),
                is_active=arguments.get("is_active"),
                is_product=arguments.get("is_product"),
                category=arguments.get("category")
            )
            item_type = "Product" if result.get("is_product") else "Service"
            status = "Active" if result.get("is_active") else "Inactive"
            text = f"""**Catalog Item Updated**
- ID: {result['id']}
- Name: {result['name']}
- Price: {result['price']}
- Type: {item_type}
- Status: {status}
- Duration: {result.get('duration_minutes', 'N/A')} minutes
- Category: {result.get('category', 'N/A')}"""

        elif name == "delete_catalog_item":
            await slotix.delete_catalog_item(arguments["item_id"])
            text = f"**Catalog item #{arguments['item_id']} deleted.**"

        # Appointment Services
        elif name == "get_appointment_services":
            result = await slotix.get_appointment_services(arguments["appointment_id"])
            if not result:
                text = f"No services attached to appointment #{arguments['appointment_id']}."
            else:
                text = f"**Services for Appointment #{arguments['appointment_id']}**\n\n"
                total = 0
                for svc in result:
                    price = float(svc.get("price_at_booking", 0))
                    total += price
                    text += f"- [ID:{svc['id']}] **{svc['item_name']}** - {svc['price_at_booking']}\n"
                text += f"\n**Total: {total}**"

        elif name == "add_service_to_appointment":
            result = await slotix.add_service_to_appointment(
                appointment_id=arguments["appointment_id"],
                catalog_item_id=arguments["catalog_item_id"]
            )
            text = f"""**Service Added to Appointment #{arguments['appointment_id']}**
- Service ID: {result['id']}
- Name: {result['item_name']}
- Price: {result['price_at_booking']}"""

        elif name == "remove_service_from_appointment":
            await slotix.remove_service_from_appointment(
                appointment_id=arguments["appointment_id"],
                service_id=arguments["service_id"]
            )
            text = f"**Service #{arguments['service_id']} removed from appointment #{arguments['appointment_id']}.**"

        else:
            text = f"Unknown tool: {name}"

        return [TextContent(type="text", text=text)]

    except ValueError as e:
        return [TextContent(type="text", text=f"**Error**: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"**Unexpected error**: {str(e)}")]


async def main_async():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for the MCP server."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
