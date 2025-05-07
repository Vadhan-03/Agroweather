import { renderWeatherUI } from './rendersWebsite.js';
import { renderForecastChart } from './chartService.js';

const refs = {
  cityInput: document.querySelector('.geo-input'),
  searchBtn: document.querySelector('.search-btn'),
};

refs.cityInput.addEventListener('input', (e) => {
  window.selectedCity = e.target.value.toLowerCase();
});

refs.searchBtn.addEventListener('click', (e) => {
  e.preventDefault();
  const city = window.selectedCity || 'tiruvallur';
  fetchWeather(city);
});

document.addEventListener('DOMContentLoaded', () => {
  fetchWeather('tiruvallur');
});

function fetchWeather(city) {
  fetch(`/api/weather/current?location=${encodeURIComponent(city)}`)
    .then((res) => res.json())
    .then((data) => {
      renderWeatherUI(data);
      renderForecastChart(data.forecast); 
    })
    .catch(() => {
      alert("Failed to load weather for this city.");
    });
}
