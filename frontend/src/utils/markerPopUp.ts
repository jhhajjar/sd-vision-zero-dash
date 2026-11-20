import { Incident } from "../services/incidentService";

export const createInfoWindowContent = (incident: Incident): HTMLElement => {
  const root = document.createElement("div");
  root.style.cssText = "padding: 8px; max-width: 250px;";

  const title = document.createElement("h4");
  title.style.cssText = "margin: 0 0 8px 0; color: #333;";
  title.textContent = incident.full_address;
  root.appendChild(title);

  const addRow = (label: string, value: string, color = "#666") => {
    const row = document.createElement("p");
    row.style.cssText = `margin: 4px 0; color: ${color};`;

    const labelElement = document.createElement("strong");
    labelElement.textContent = `${label}: `;
    row.append(labelElement, value);
    root.appendChild(row);
  };

  addRow("Date", incident.date_time);
  addRow("Charge", incident.charge_desc || "N/A");
  addRow("Injured", String(incident.injured));
  addRow(
    "Killed",
    String(incident.killed),
    incident.killed > 0 ? "#dc3545" : "#666",
  );

  return root;
};
