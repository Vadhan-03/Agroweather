export async function sendWeatherAdvisory() {
    try {
        const button = document.querySelector('.send-advisory-btn');
        if (!button) {
            throw new Error('Send button not found');
        }

        button.disabled = true;
        button.textContent = 'Sending...';

        // Get weather data with null checks
        const getElementText = (selector, defaultValue = 'N/A') => {
            const element = document.querySelector(selector);
            return element ? element.textContent : defaultValue;
        };

        const getElementValue = (selector, defaultValue = 'N/A') => {
            const element = document.getElementById(selector);
            return element ? element.value : defaultValue;
        };

        // Get weather data from the page
        const weatherData = {
            city: getElementText('.weather__location-city'),
            temperature: getElementText('.day-stats__temperature-value'),
            windSpeed: getElementText('.weather__wind-kph'),
            windDirection: getElementText('.weather__wind-dir'),
            rainChance: getElementText('.weather__rain'),
            humidity: getElementText('.day-stats__humidity'),
            date: getElementValue('forecast-date', new Date().toISOString().split('T')[0])
        };

        if (Object.values(weatherData).every(value => value === 'N/A')) {
            throw new Error('No weather data available to send');
        }

        // Send to backend
        const response = await fetch('/send-advisory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(weatherData)
        });

        const result = await response.json();

        if (result.success) {
            alert('Weather advisory sent successfully!');
        } else {
            throw new Error(result.error || 'Failed to send advisory');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to send weather advisory: ' + error.message);
    } finally {
        const button = document.querySelector('.send-advisory-btn');
        button.disabled = false;
        button.textContent = 'Send Advisory';
    }
}
