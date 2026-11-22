import { useEffect, useRef, useState } from "react";

const GOOGLE_MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
let mapsLoader;

function loadGoogleMaps() {
  if (window.google?.maps) return Promise.resolve(window.google.maps);
  if (!GOOGLE_MAPS_KEY)
    return Promise.reject(
      new Error(
        "Add VITE_GOOGLE_MAPS_API_KEY to frontend/.env to enable the map.",
      ),
    );
  if (!mapsLoader) {
    mapsLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(GOOGLE_MAPS_KEY)}&v=weekly`;
      script.async = true;
      script.onload = () => resolve(window.google.maps);
      script.onerror = () => {
        mapsLoader = null;
        reject(
          new Error(
            "Google Maps could not load. Check the API key and Maps JavaScript API access.",
          ),
        );
      };
      document.head.appendChild(script);
    });
  }
  return mapsLoader;
}

// Free reverse geocoding (OpenStreetMap Nominatim). No API key or billing needed.
// Usage policy: max ~1 request/second, no search-as-you-type.
async function reverseGeocode(lat, lng) {
  const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=18&accept-language=en&lat=${lat}&lon=${lng}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.display_name || "";
}

// Free forward geocoding: address text -> coordinates (India only; remove countrycodes to search worldwide).
async function nominatimSearch(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=in&accept-language=en&q=${encodeURIComponent(query)}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data[0]
    ? {
        lat: parseFloat(data[0].lat),
        lng: parseFloat(data[0].lon),
        name: data[0].display_name,
      }
    : null;
}

// OpenStreetMap often lacks house numbers and small streets, so if the full
// address finds nothing, retry with progressively shorter versions of it.
async function searchAddressText(query) {
  const withoutNumber = query.replace(/^\s*[\d\/\-\s]+[,\s]+/, "").trim();
  const parts = withoutNumber
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  const candidates = [query.trim()];
  for (let i = 0; i < parts.length; i++)
    candidates.push(parts.slice(i).join(", "));
  const tried = new Set();
  for (const candidate of candidates) {
    if (!candidate || tried.has(candidate)) continue;
    tried.add(candidate);
    const found = await nominatimSearch(candidate);
    if (found) return { ...found, approximate: candidate !== query.trim() };
    await new Promise((r) => setTimeout(r, 1100)); // respect Nominatim's 1 request/second limit
  }
  return null;
}

export default function GoogleMapPicker({ latitude, longitude, onSelect }) {
  const mapElement = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  const lookupId = useRef(0);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [accuracy, setAccuracy] = useState(null);
  onSelectRef.current = onSelect;

  // Look up the street address for a point and send it to the parent form.
  async function fillAddress(coordinates) {
    const id = ++lookupId.current; // ignore stale responses if the user clicks again quickly
    try {
      const address = await reverseGeocode(
        coordinates.latitude,
        coordinates.longitude,
      );
      if (id !== lookupId.current) return;
      if (address) {
        setError("");
        onSelectRef.current({ ...coordinates, location: address });
      } else {
        setError(
          "No street address found for this point. You can enter the street manually.",
        );
      }
    } catch {
      if (id !== lookupId.current) return;
      setError("The address lookup failed. You can enter the street manually.");
    }
  }

  // Send coordinates immediately, then fetch the address.
  function selectPoint(lat, lng) {
    const coordinates = {
      latitude: Number(lat).toFixed(6),
      longitude: Number(lng).toFixed(6),
    };
    onSelectRef.current(coordinates);
    fillAddress(coordinates);
  }

  // Create the marker if needed (draggable), otherwise move it.
  function placeMarker(position) {
    const maps = window.google.maps;
    if (!markerRef.current) {
      markerRef.current = new maps.Marker({
        map: mapRef.current,
        position,
        draggable: true,
      });
      markerRef.current.addListener("dragend", (event) => {
        selectPoint(event.latLng.lat(), event.latLng.lng());
      });
    } else {
      markerRef.current.setMap(mapRef.current);
      markerRef.current.setPosition(position);
    }
  }

  useEffect(() => {
    let clickListener;
    let cancelled = false;
    loadGoogleMaps()
      .then((maps) => {
        if (cancelled || !mapElement.current) return;
        const hasPoint = latitude !== "" && longitude !== "";
        const center = hasPoint
          ? { lat: Number(latitude), lng: Number(longitude) }
          : { lat: 20.5937, lng: 78.9629 };
        const map = new maps.Map(mapElement.current, {
          center,
          zoom: hasPoint ? 16 : 5,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        });
        mapRef.current = map;
        if (hasPoint) placeMarker(center);
        clickListener = map.addListener("click", (event) => {
          const point = { lat: event.latLng.lat(), lng: event.latLng.lng() };
          placeMarker(point);
          selectPoint(point.lat, point.lng);
        });
        setReady(true);
      })
      .catch((err) => setError(err.message));
    return () => {
      cancelled = true;
      if (clickListener) clickListener.remove();
    };
  }, []);

  // Keep the marker in sync when latitude/longitude change from outside (e.g. form reset).
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const hasPoint = latitude !== "" && longitude !== "";
    if (!hasPoint) {
      markerRef.current?.setMap(null);
      return;
    }
    const point = { lat: Number(latitude), lng: Number(longitude) };
    placeMarker(point);
    mapRef.current.panTo(point);
  }, [latitude, longitude, ready]);

  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  async function searchAddress() {
    const text = query.trim();
    if (!text || !mapRef.current) return;
    setError("");
    setSearching(true);
    try {
      const found = await searchAddressText(text);
      if (!found) {
        setError(
          "No match found. Try adding the area and city, or click the map.",
        );
        return;
      }
      const point = { lat: found.lat, lng: found.lng };
      placeMarker(point);
      mapRef.current.panTo(point);
      mapRef.current.setZoom(17);
      const coordinates = {
        latitude: found.lat.toFixed(6),
        longitude: found.lng.toFixed(6),
      };
      if (found.approximate) {
        // Only a nearby area matched: keep the user's full typed address and ask them to place the pin.
        onSelectRef.current({ ...coordinates, location: text });
        setError(
          "Exact street not found, so the pin is at the nearest area. Drag the pin to the exact spot.",
        );
      } else {
        onSelectRef.current({ ...coordinates, location: found.name });
      }
    } catch {
      setError("Address search failed. Click the map to pin the spot instead.");
    } finally {
      setSearching(false);
    }
  }

  function useCurrentLocation() {
    setError("");
    if (!navigator.geolocation) {
      setError("Location access is not supported by this browser.");
      return;
    }
    setAccuracy(null);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const point = { lat: coords.latitude, lng: coords.longitude };
        if (mapRef.current) {
          placeMarker(point);
          mapRef.current.panTo(point);
          mapRef.current.setZoom(coords.accuracy > 1000 ? 13 : 16);
        }
        setAccuracy(Math.round(coords.accuracy));
        selectPoint(coords.latitude, coords.longitude);
      },
      () =>
        setError(
          "Could not get your location. Allow location access or click the map.",
        ),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    );
  }

  return (
    <div className="md:col-span-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-slate-700">
          Pin the issue on Google Maps (optional)
        </p>
        <button
          type="button"
          onClick={useCurrentLocation}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          Use my location
        </button>
      </div>
      <div className="mb-2 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              searchAddress();
            }
          }}
          placeholder="Search area or street, e.g. Fairlands, Salem"
          className="w-full rounded-lg border px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={searchAddress}
          disabled={searching}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </div>
      <div
        ref={mapElement}
        className="h-72 w-full rounded-lg border bg-slate-100"
      />
      {error && <p className="mt-2 text-sm text-amber-700">{error}</p>}
      {accuracy !== null && accuracy > 100 && (
        <p className="mt-2 text-sm text-amber-700">
          Your device located you only within about{" "}
          {accuracy >= 1000
            ? `${(accuracy / 1000).toFixed(1)} km`
            : `${accuracy} m`}
          . Drag the pin to the exact spot.
        </p>
      )}
      {latitude !== "" && longitude !== "" && (
        <p className="mt-2 text-xs text-slate-500">
          Selected coordinates: {latitude}, {longitude}
        </p>
      )}
      {!GOOGLE_MAPS_KEY && (
        <p className="mt-2 text-xs text-slate-500">
          Configure <code>VITE_GOOGLE_MAPS_API_KEY</code> in{" "}
          <code>frontend/.env</code> to show the map.
        </p>
      )}
    </div>
  );
}
