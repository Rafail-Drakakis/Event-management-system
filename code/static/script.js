const API_URL = "http://localhost:5000";

// Helper function to display notifications
function showMessage(message, type = "info") {
  // Remove existing notifications first
  document.querySelectorAll('.notification').forEach(n => n.remove());
  
  const messageDiv = document.createElement("div");
  messageDiv.className = `notification ${type}`;
  messageDiv.textContent = message;
  document.body.appendChild(messageDiv);
  
  // Remove the message after 3 seconds
  setTimeout(() => {
    if (messageDiv.parentNode) {
      messageDiv.remove();
    }
  }, 3000);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  update_event_chooser("bookEventIdselect");
  update_event_chooser("searchSeatsIdselect");
  update_event_chooser("cancelEventIdselect");
  update_event_chooser("pes");
  table_all();
});
// Helper function to display the tables
async function table_render(table_name, table_json) {
  try {
    let jsonData;
    if (table_json == null) {
      const response = await fetch(`${API_URL}/` + table_name, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      jsonData = await response.json();
    } else {
      jsonData = table_json;
    }

    if (!Object.keys(jsonData).length) {
      return;
    }
    // Get the container element where the table will be inserted
    let container = document.getElementById(table_name + "_container");
    // Clear prvious render
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    // Append the table title to the container element
    let head = document.createElement("h2");
    head.textContent =
      table_name.charAt(0).toUpperCase() + table_name.slice(1) + " Table";
    container.appendChild(head);
    // Create the table element
    let table = document.createElement("table");
    // Get the keys (column names) of the first object in the JSON data
    let cols = Object.keys(jsonData[0]);
    // Create the header element
    let thead = document.createElement("thead");
    let tr = document.createElement("tr");
    // Loop through the column names and create header cells
    cols.forEach((item) => {
      let th = document.createElement("th");
      th.innerText = item; // Set the column name as the text of the header cell
      tr.appendChild(th); // Append the header cell to the header row
    });
    thead.appendChild(tr); // Append the header row to the header
    table.append(tr); // Append the header to the table
    // Loop through the JSON data and create table rows
    jsonData.forEach((item) => {
      let tr = document.createElement("tr");

      // Get the values of the current object in the JSON data
      let vals = Object.values(item);
      // Loop through the values and create table cells
      vals.forEach((elem) => {
        let td = document.createElement("td");
        td.innerText = elem; // Set the value as the text of the table cell
        tr.appendChild(td); // Append the table cell to the table row
      });
      table.appendChild(tr); // Append the table row to the table
    });
    container.appendChild(table); // Append the table to the container element
  } catch (error) {
    showMessage("Internal error rendering " + table_name + " table");
    console.log("Error", error.stack);
    console.log("Error", error.name);
    console.log("Error", error.message);
  }
}

function table_all() {
  table_render("customers", null);
  table_render("events", null);
  table_render("tickets", null);
  table_render("reservations", null);
}

// Helper function to populate tickets
async function add_ticket(
  t_eid,
  t_type,
  t_price,
  t_availability,
  t_seat_number,
) {
  const maxRetries = 3;
  let retries = 0;
  var state = 0;
  var tid1 = null;
  
  while (retries < maxRetries) {
    try {
      if (Number(state) == 0) {
        const ticket = {
          type: t_type,
          price: t_price,
          availability: t_availability,
          seat_number: t_seat_number,
        };
        const response = await fetch(`${API_URL}/tickets`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(ticket),
        });
        const result = await response.json();
        if (response.status === 201) {
          state = 1;
          tid1 = result.tid;
        } else {
          console.log("Ticket creation failed:", result.message);
          throw new Error(result.message || "Ticket creation failed");
        }
      }
      if (Number(state) == 1) {
        const has = {
          tid: tid1,
          eid: t_eid,
        };
        const response = await fetch(`${API_URL}/has`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(has),
        });
        const result = await response.json();
        if (response.status === 201) {
          return true;
        } else {
          console.log("Ticket-event link failed:", result.message);
          throw new Error(result.message || "Ticket-event link failed");
        }
      }
    } catch (error) {
      retries++;
      console.log(`Error adding ticket (attempt ${retries}/${maxRetries}):`, error.message);
      if (retries >= maxRetries) {
        showMessage(`Failed to add ticket after ${maxRetries} attempts`, "error");
        return false;
      }
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  return false;
}
async function update_event_chooser(container_name) {
  const maxRetries = 3;
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const response = await fetch(`${API_URL}/eventnames`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      let jsonData = await response.json();
      let container = document.getElementById(container_name);
      
      if (!container) {
        console.error(`Container ${container_name} not found`);
        return;
      }
      
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }

      if (container_name == "pes") {
        var option = document.createElement("option");
        option.value = "All";
        option.innerHTML = "All events";
        container.appendChild(option);
      }

      for (let i = 0; i < jsonData.length; i++) {
        var option = document.createElement("option");
        option.value = jsonData[i].eid;
        option.innerHTML = jsonData[i].name;
        container.appendChild(option);
      }
      return;
    } catch (error) {
      retries++;
      console.log(`Error updating ${container_name} (attempt ${retries}/${maxRetries}):`, error.message);
      if (retries >= maxRetries) {
        showMessage(`Failed to load events for ${container_name}`, "error");
        return;
      }
      // Wait a bit before retrying
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
async function update_tickets_chooser() {
  var vip_price = "";
  var front_price = "";
  var normal_price = "";
  var eid = document.getElementById("bookEventIdselect").value;
  var tries = 5;
  event_loop: while (tries > 0) {
    tries--;
    try {
      let response = await fetch(
        `${API_URL}/ticket_price/` + eid + "/" + "VIP",
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        },
      );

      let result = await response.json();
      if (response.status != 200) {
        throw response.status;
      }
      vip_price = String(result.price) + "€";
      response = await fetch(
        `${API_URL}/ticket_price/` + eid + "/" + "FrontRow",
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        },
      );
      result = await response.json();
      if (response.status != 200) {
        throw response.status;
      }
      front_price = String(result.price) + "€";
      response = await fetch(
        `${API_URL}/ticket_price/` + eid + "/" + "Normal",
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        },
      );
      result = await response.json();
      if (response.status != 200) {
        throw response.status;
      }
      normal_price = String(result.price) + "€";
      break event_loop;
    } catch (error) {
      showMessage("error updating checkbox");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  }
  if (tries <= 0) {
    console.log("error");
    return;
  }
  let container = document.getElementById("bookTicketsFormdiv");
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
  var ticket_num = document.getElementById("numOfTickets").value;
  for (let i = 0; i < ticket_num; i++) {
    var label = document.createElement("label");
    label.innerText = "Type for ticket #" + (Number(i) + 1) + ":";
    var label2 = document.createElement("label");
    label2.innerText = "\n";
    var t_type = document.createElement("select");

    var type1 = document.createElement("option");
    type1.value = "VIP";
    type1.innerHTML = "VIP" + "(" + vip_price + ")";
    t_type.appendChild(type1);

    var type2 = document.createElement("option");
    type2.value = "FrontRow";
    type2.innerHTML = "Front Row" + "(" + front_price + ")";
    t_type.appendChild(type2);

    var type3 = document.createElement("option");
    type3.value = "Normal";
    type3.innerHTML = "Normal" + "(" + normal_price + ")";
    t_type.appendChild(type3);

    t_type.id = "ticket" + i;
    container.appendChild(label);
    container.appendChild(t_type);
    container.appendChild(label2);
  }
  return;
}
// Function to handle adding a new customer
document
  .getElementById("addCustomerForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const customer = {
      mail: document.getElementById("customerEmail").value,
      credit_info: document.getElementById("customerCredit").value,
      f_name: document.getElementById("customerFirstName").value,
      l_name: document.getElementById("customerLastName").value,
    };
    try {
      const response = await fetch(`${API_URL}/customers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(customer),
      });
      const result = await response.json();
      if (response.status === 201) {
        showMessage(result.message, "success");
        setTimeout(table_all, 500);
        document.getElementById("addCustomerForm").reset();
      } else {
        showMessage(result.message, "error");
      }
    } catch (error) {
      showMessage("Error adding customer. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to handle adding a new event
document
  .getElementById("addEventForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const event1 = {
      name: document.getElementById("eventName").value,
      type: document.getElementById("eventType").value,
      time: document.getElementById("eventTime").value,
      date: document.getElementById("eventDate").value,
      capacity: document.getElementById("eventCapacity").value,
    };
    let capacity = document.getElementById("eventCapacity").value;
    let vip_num = document.getElementById("VIP_Capacity").value;
    let front_num = document.getElementById("FrontRow_Capacity").value;
    let normal_num = document.getElementById("Normal_Capacity").value;
    let vip_price = document.getElementById("VIP_Price").value;
    let front_price = document.getElementById("FrontRow_Price").value;
    let normal_price = document.getElementById("Normal_Price").value;
    if (!isFinite(vip_num) || !isFinite(front_num) || !isFinite(normal_num)) {
      showMessage("Error: Number of seats given isn't integer!", "error");
      return;
    }
    if (
      Number(vip_num) + Number(front_num) + Number(normal_num) !=
      Number(capacity)
    ) {
      showMessage("Error: Number of seats don't add up to capacity!", "error");
      return;
    }
    try {
      const response = await fetch(`${API_URL}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event1),
      });
      const result = await response.json();
      let event_id = result.id;
      if (response.status === 201) {
        //event added to db
        for (let i = 0; i < Number(vip_num); i++) {
          add_ticket(event_id, "VIP", vip_price, 1, i + 1);
        }
        for (let i = 0; i < Number(front_num); i++) {
          add_ticket(
            event_id,
            "FrontRow",
            front_price,
            1,
            i + 1 + Number(vip_num),
          );
        }
        for (let i = 0; i < Number(normal_num); i++) {
          add_ticket(
            event_id,
            "Normal",
            normal_price,
            1,
            i + 1 + Number(vip_num) + Number(front_num),
          );
        }
        showMessage(result.message, "success");
        setTimeout(table_all, 500);
        update_event_chooser("bookEventIdselect");
        update_event_chooser("searchSeatsIdselect");
        update_event_chooser("cancelEventIdselect");
        update_event_chooser("pes");
        document.getElementById("addEventForm").reset();
      } else {
        showMessage(result.message, "error");
      }
    } catch (error) {
      showMessage("Error adding event. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to search for available seats
document
  .getElementById("searchSeatsForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const eventId = document.getElementById("searchSeatsIdselect").value;
    try {
      const response = await fetch(`${API_URL}/available_seats/${eventId}`);
      const seats = await response.json();
      if (Object.keys(seats).length > 0) {
        table_render("availableSeatsResult", seats);
        showMessage(
          `Found ${
            Object.keys(seats).length
          } available seats for event ID ${eventId}.`,
          "success",
        );
      } else {
        showMessage("No available seats found for this event.", "info");
      }
    } catch (error) {
      showMessage("Error fetching available seats. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to book tickets for an event
document
  .getElementById("bookTicketsForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    var arr = [];
    for (let i = 0; i < document.getElementById("numOfTickets").value; i++) {
      arr.push(document.getElementById("ticket" + i).value);
    }
    const counts = {};
    arr.forEach(function (x) {
      counts[x] = (counts[x] || 0) + 1;
    });
    const booking = {
      eid: document.getElementById("bookEventIdselect").value,
      cid: document.getElementById("customerIdmail").value,
      date: new Date().toISOString().split("T")[0], // Current date
      total_price: 0, //placeholder
      tickets_number: document.getElementById("numOfTickets").value,
      tickets: counts,
    };
    try {
      const response = await fetch(`${API_URL}/reserve_tickets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(booking),
      });
      const result = await response.json();
      if (response.status === 201) {
        showMessage(result.message, "success");
        setTimeout(table_all, 500);
        document.getElementById("bookTicketsForm").reset();
        document.getElementById("bookTicketsFormdiv").innerHTML = "";
      } else {
        showMessage(result.message, "error");
      }
    } catch (error) {
      showMessage("Error booking tickets. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to cancel a reservation
document
  .getElementById("cancelReservationForm")
  .addEventListener("submit", async (e) => {
    console.log("hello from cancel 2");
    e.preventDefault();
    const customerEmail = document.getElementById("customerEmailCancel").value;
    try {
      // Make a POST request with the email as the body data
      const response = await fetch(`${API_URL}/cancel_reservation`, {
        method: "POST", // POST request
        headers: {
          "Content-Type": "application/json", // Set content type to JSON
        },
        body: JSON.stringify({ email: customerEmail }), // Send the email as JSON
      });
      const result = await response.json();
      if (response.status === 200) {
        showMessage(result.message, "success");
        setTimeout(table_all, 500);
        document.getElementById("cancelReservationForm").reset();
      } else {
        showMessage(result.message, "error");
      }
    } catch (error) {
      showMessage("Error canceling reservation. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });

// Function to cancel an event
document
  .getElementById("cancelEventForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log("hello from cancel 1");
    const eventid = document.getElementById("cancelEventIdselect").value;
    try {
      const response = await fetch(`${API_URL}/cancel_event/${eventid}`, {
        method: "GET",
      });
      const result = await response.json();
      if (response.status === 200) {
        const eventid = document.getElementById("cancelEventIdselect").value;
        removeEventFromDropdown("cancelEventIdselect", eventid);
        removeEventFromDropdown("bookEventIdselect", eventid);
        removeEventFromDropdown("searchSeatsIdselect", eventid);
        removeEventFromDropdown("pes", eventid);
        showMessage("Event cancelled", "success");
        setTimeout(table_all, 500);
      } else {
        showMessage(result.message, "error");
      }
    } catch (error) {
      showMessage("Error canceling event. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
//  to remove event from dropdowns
function removeEventFromDropdown(selectElementId, eventId) {
  const eventSelect = document.getElementById(selectElementId);
  const optionToRemove = eventSelect.querySelector(
    `option[value="${eventId}"]`,
  );
  if (optionToRemove) {
    optionToRemove.remove();
  }
}

// Function to view tickets left for all events
document.getElementById("refresh_render").addEventListener("click", () => {
  table_all();
});
// Function to view event profits
document.getElementById("profitsForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  console.log("start here?");
  const profit_info = {
    eid: document.getElementById("pes").value,
    type: document.getElementById("pts").value,
  };
  console.log("here?");
  try {
    const response = await fetch(`${API_URL}/revenue_event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profit_info),
    });
    console.log("here here?");
    const result = await response.json();
    if (response.status === 200) {
      document.getElementById("eventSProfits_container").innerText =
        JSON.stringify(result.total_revenue, null, 2);
      showMessage("Successfully retrieved profits", "success");
    } else {
      showMessage(result.message, "error");
    }
  } catch (error) {
    showMessage("Error retrieving profits. Try again.", "error");
    console.log("Error", error.stack);
    console.log("Error", error.name);
    console.log("Error", error.message);
  }
});

document
  .getElementById("viewReservationsForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const reservation_constrains = {
      start_date: document.getElementById("eventDateS").value,
      end_date: document.getElementById("eventDateF").value,
    };
    try {
      const response = await fetch(`${API_URL}/active_reserve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reservation_constrains),
      });
      const result = await response.json();
      if (response.status === 200) {
        if (Object.keys(result).length > 0) {
          table_render("ActiveReservationsResult", result);
          showMessage(
            `Found ${
              Object.keys(result).length
            } reservations that fit the criteria.`,
            "success",
          );
        }
      } else {
        showMessage("No active reservations found.", "info");
      }
    } catch (error) {
      showMessage("Error viewing reservation. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to view the most popular event
document
  .getElementById("mostPopularEvent")
  .addEventListener("click", async () => {
    try {
      const response = await fetch(`${API_URL}/most_popular_event`);
      const event = await response.json();
      console.log(event);
      if (event.name) {
        showMessage(
          `Most popular event is ${event.name} with ${event.reservations_count} reservations.`,
          "success",
        );
      } else {
        showMessage("No popular events found.", "info");
      }
    } catch (error) {
      showMessage("Error fetching most popular event. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });
// Function to view the highest profit event within a date range
document
  .getElementById("highestProfitEvent")
  .addEventListener("click", async () => {
    const startDate = prompt("Enter start date (YYYY-MM-DD):");
    const endDate = prompt("Enter end date (YYYY-MM-DD):");
    try {
      const response = await fetch(`${API_URL}/highest_revenue_event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
        }),
      });
      const event = await response.json();
      if (event.name) {
        showMessage(
          `Highest profit event is ${event.name} with revenue of ${event.revenue}€.`,
          "success",
        );
      } else {
        showMessage("No events found for the given time period.", "info");
      }
    } catch (error) {
      showMessage("Error fetching highest profit event. Try again.", "error");
      console.log("Error", error.stack);
      console.log("Error", error.name);
      console.log("Error", error.message);
    }
  });