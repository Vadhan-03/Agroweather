export function renderWeatherUI(data) {
  // DOM Elements
  const elements = {
      // Temperature block
      temperature: document.querySelector('.day-stats__temperature-value'),
      feelsLike: document.querySelector('.day-stats__feelslike-value'),
      cloud: document.querySelector('.day-stats__clouds'),
      humidity: document.querySelector('.day-stats__humidity'),
      uvIndex: document.querySelector('.uv-header__value'),

      // Location & title
      title: document.querySelector('.weather__primary-title'),
      city: document.querySelector('.weather__location-city'),
      country: document.querySelector('.weather__location-country'),
      date: document.querySelector('.weather__location-date'),

      // Weather details
      windDir: document.querySelector('.weather__wind-dir'),
      windKph: document.querySelector('.weather__wind-kph'),
      pressure: document.querySelector('.weather__pressure-mb'),
      rain: document.querySelector('.weather__rain'),
      snow: document.querySelector('.weather__snow'),
      maxTemp: document.querySelector('.weather__max-temp'),
      minTemp: document.querySelector('.weather__min-temp'),

      // Main container for background
      main: document.querySelector('main')
  };

  // Update temperature stats
  if (elements.temperature) elements.temperature.textContent = data.temp;
  if (elements.feelsLike) elements.feelsLike.textContent = data.feels_like;
  if (elements.cloud) elements.cloud.textContent = data.cloud;
  if (elements.humidity) elements.humidity.textContent = data.humidity;
  if (elements.uvIndex) elements.uvIndex.textContent = data.uv_index;

  // Update location and title
  if (elements.title) elements.title.textContent = data.weather;
  if (elements.city && elements.country && elements.date && data.location) {
      const [city, country] = data.location.split(',');
      elements.city.textContent = city.trim();
      elements.country.textContent = country.trim();
      elements.date.textContent = data.datetime;
  }

  // Update weather details
  if (elements.windDir) elements.windDir.textContent = data.wind_dir;
  if (elements.windKph) elements.windKph.textContent = data.wind_kph;
  if (elements.pressure) elements.pressure.textContent = data.pressure_mb;
  if (elements.rain) elements.rain.textContent = data.rain;
  if (elements.snow) elements.snow.textContent = data.snow;
  if (elements.maxTemp) elements.maxTemp.textContent = data.max_temp;
  if (elements.minTemp) elements.minTemp.textContent = data.min_temp;

  // Update forecast items
  const forecastItems = document.querySelectorAll('.forecast-item');
  data.forecast.slice(0, 5).forEach((hour, index) => {
      const item = forecastItems[index];
      if (item) {
          const timeElement = item.querySelector('.forecast__time');
          const tempElement = item.querySelector('.forecast__temperature--value');
          const windElement = item.querySelector('.forecast__wind-value');

          if (timeElement) timeElement.textContent = hour.time;
          if (tempElement) tempElement.textContent = hour.temp;
          if (windElement) windElement.textContent = hour.wind_kph;
      }
  });

  // Update background based on weather condition
  if (elements.main) {
    elements.main.className = ''; // Reset previous classes
    const weatherText = data.weather.toLowerCase();


    const weatherConditions = {
        sunny: ['sunny'],
        clear: ['clear'],
        drizzle: ['moderate rain at times'],
        cloudy: ['partly cloudy'],
        showers: ['light rain shower'],
        rain: [
            'patchy rain nearby',
            'patchy light rain in area with thunder',
            'moderate or heavy rain in area with thunder'
        ],
        thunder: ['thundery outbreaks in nearby'],
        mist: ['mist'],
        overcast: ['overcast'],
        fog: ['fog']
    };

      // Find and apply matching weather condition class
      Object.entries(weatherConditions).forEach(([className, keywords]) => {
        if (keywords.some(keyword => weatherText.includes(keyword.toLowerCase()))) {
            elements.main.classList.add(className);
            document.body.className = `${className}-theme`;
        }
      });
  }
}