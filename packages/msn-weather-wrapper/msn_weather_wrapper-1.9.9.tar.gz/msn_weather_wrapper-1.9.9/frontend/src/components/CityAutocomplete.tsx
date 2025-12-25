import { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from 'react';
import { cities } from '../data/cities';
import type { City } from '../types';
import './CityAutocomplete.css';

interface CityAutocompleteProps {
  onCitySelect: (city: City) => void;
}

export default function CityAutocomplete({ onCitySelect }: CityAutocompleteProps) {
  const [inputValue, setInputValue] = useState<string>('');
  const [filteredCities, setFilteredCities] = useState<City[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const value = e.target.value;
    setInputValue(value);
    setSelectedIndex(-1);

    if (value.trim().length > 0) {
      const filtered = cities.filter((city: City) =>
        city.name.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 8);
      setFilteredCities(filtered);
      setShowSuggestions(true);
    } else {
      setFilteredCities([]);
      setShowSuggestions(false);
    }
  };

  const handleCitySelect = (city: City): void => {
    setInputValue(`${city.name}, ${city.country}`);
    setShowSuggestions(false);
    onCitySelect(city);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>): void => {
    if (!showSuggestions || filteredCities.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev: number) =>
        prev < filteredCities.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev: number) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < filteredCities.length) {
        handleCitySelect(filteredCities[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  return (
    <div className="autocomplete-wrapper" ref={wrapperRef}>
      <label htmlFor="city-search" className="sr-only">
        Search for a city
      </label>
      <input
        id="city-search"
        type="text"
        className="city-input"
        placeholder="Search for a city..."
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (filteredCities.length > 0) {
            setShowSuggestions(true);
          }
        }}
        role="combobox"
        aria-expanded={showSuggestions && filteredCities.length > 0}
        aria-controls="city-suggestions"
        aria-activedescendant={
          selectedIndex >= 0 ? `city-option-${selectedIndex}` : undefined
        }
        aria-autocomplete="list"
        aria-label="Search for a city to get weather information"
      />

      {showSuggestions && filteredCities.length > 0 && (
        <ul
          id="city-suggestions"
          className="suggestions-list"
          role="listbox"
          aria-label="City suggestions"
        >
          {filteredCities.map((city: City, index: number) => (
            <li
              id={`city-option-${index}`}
              key={`${city.name}-${city.country}`}
              className={`suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleCitySelect(city)}
              onMouseEnter={() => setSelectedIndex(index)}
              role="option"
              aria-selected={index === selectedIndex}
            >
              <span className="city-name">{city.name}</span>
              <span className="city-country">{city.country}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
