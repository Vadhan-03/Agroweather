import { renderWeatherUI } from './rendersWebsite.js';
import { sendWeatherAdvisory } from './advisory.js';

const refs = {
  cityInput: document.querySelector('.geo-input'),
  searchBtn: document.querySelector('.search-btn'),
  sendBtn: document.querySelector('.send-advisory-btn'),
  mainEl: document.querySelector('main'),
  primaryTitle: document.querySelector('.weather__primary-title'),
  primaryStats: document.querySelector('.weather__primary-stats'),
  locationText: document.querySelector('.weather__location-text'),
  datePicker: document.getElementById('forecast-date')
};

// Populate the date picker with 14 days
function populateDatePicker() {
  const datePicker = document.getElementById('forecast-date');
  const today = new Date();
  datePicker.innerHTML = ''; // Clear existing options
  for (let i = 0; i < 14; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);

    const option = document.createElement('option');
    option.value = date.toISOString().split('T')[0]; // Format: YYYY-MM-DD
    option.textContent = date.toDateString(); // Format: Day, Month Date, Year
    datePicker.appendChild(option);
  }
}

// Update the dashboard with weather data for the selected date
async function updateDashboard(city) {
  const selectedDate = document.getElementById('forecast-date').value;
  const queryParams = new URLSearchParams({
    location: encodeURIComponent(city),
    date: selectedDate
  });

  try {
    const response = await fetch(`/api/weather/current?${queryParams}`);
    if (!response.ok) {
      throw new Error('Failed to load weather data');
    }
    const data = await response.json();
    
    // Render UI
    renderWeatherUI(data);

    // Update location text with data from response
    if (data.location && data.datetime) {
      const [cityName, country] = data.location.split(',');
      refs.locationText.innerHTML = `
        <span class="weather__location-city">${cityName.trim()}</span>,
        <span class="weather__location-country">${country.trim()}</span>,
        <span class="weather__location-date">${data.datetime}</span>
      `;
    }

  } catch (error) {
    console.error('Error:', error);
    alert('Failed to update weather data');
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  populateDatePicker();
  const city = refs.cityInput.value.trim() || 'tiruvallur';
  updateDashboard(city);

  // Date picker change event
  refs.datePicker.addEventListener('change', () => {
    const city = refs.cityInput.value.trim() || 'tiruvallur';
    updateDashboard(city);
  });

  // Search button click event
  refs.searchBtn.addEventListener('click', e => {
    e.preventDefault();
    const city = refs.cityInput.value.trim() || 'tiruvallur';
    updateDashboard(city);
  });

  // SMS button click event
  refs.sendBtn.addEventListener('click', sendWeatherAdvisory);
});