'use client';

import { useState } from 'react';
import Navbar from "../../components/Navbar";
import { Card } from '../../types/card';

// Mock data for Clash Royale cards
const ALL_CARDS: Card[] = [
  { id: 1, name: 'Knight', rarity: 'Common', elixir: 3, type: 'Troop', description: 'Tough melee fighter.' },
  { id: 2, name: 'Archers', rarity: 'Common', elixir: 3, type: 'Troop', description: 'Ranged attackers.' },
  { id: 3, name: 'Goblins', rarity: 'Common', elixir: 2, type: 'Troop', description: 'Fast melee attackers.' },
  { id: 4, name: 'Giant', rarity: 'Epic', elixir: 5, type: 'Troop', description: 'Slow melee tank.' },
  { id: 5, name: 'Pekka', rarity: 'Legendary', elixir: 7, type: 'Troop', description: 'Heavy armored melee unit.' },
  { id: 6, name: 'Minions', rarity: 'Common', elixir: 3, type: 'Troop', description: 'Air attackers.' },
  { id: 7, name: 'Fireball', rarity: 'Rare', elixir: 4, type: 'Spell', description: 'Area damage spell.' },
  { id: 8, name: 'Barbarians', rarity: 'Common', elixir: 5, type: 'Troop', description: 'Melee attackers.' },
  { id: 9, name: 'Skeleton Army', rarity: 'Epic', elixir: 3, type: 'Troop', description: 'Spawns multiple skeletons.' },
  { id: 10, name: 'Archer Queen', rarity: 'Legendary', elixir: 3, type: 'Troop', description: 'Ranged support unit.' },
  { id: 11, name: 'Hog Rider', rarity: 'Epic', elixir: 4, type: 'Troop', description: 'Fast melee unit targeting buildings.' },
  { id: 12, name: 'Musketeer', rarity: 'Rare', elixir: 4, type: 'Troop', description: 'Ranged attacker.' },
  { id: 13, name: 'Ice Wizard', rarity: 'Legendary', elixir: 3, type: 'Troop', description: 'Slows nearby enemies.' },
  { id: 14, name: 'The Log', rarity: 'Legendary', elixir: 2, type: 'Spell', description: 'Area damage and knockback.' },
  { id: 15, name: 'Ice Spirit', rarity: 'Common', elixir: 1, type: 'Troop', description: 'Freezes nearby enemies.' },
  { id: 16, name: 'Fire Spirit', rarity: 'Common', elixir: 1, type: 'Troop', description: 'Burns nearby enemies.' },
  { id: 17, name: 'Bomber', rarity: 'Common', elixir: 2, type: 'Troop', description: 'Ranged area damage.' },
  { id: 18, name: 'Cannon', rarity: 'Common', elixir: 3, type: 'Building', description: 'Defensive building.' },
  { id: 19, name: 'Tesla', rarity: 'Common', elixir: 4, type: 'Building', description: 'Attacks air and ground.' },
  { id: 20, name: 'Goblin Hut', rarity: 'Rare', elixir: 5, type: 'Building', description: 'Spawns goblins.' },
];



interface RecommendationResponse {
  recommended_cards: string[];
  win_probability: number;
  confidence: number;
}

export default function BuilderPage() {
  const [selectedCards, setSelectedCards] = useState<Card[]>([]);
  const [availableCards, setAvailableCards] = useState<Card[]>(ALL_CARDS);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [winProbability, setWinProbability] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Calculate total elixir cost
  const totalElixir = selectedCards.reduce((sum, card) => sum + card.elixir, 0);

  // Handle card selection
  const handleSelectCard = (card: Card) => {
    if (selectedCards.length < 8 && !selectedCards.some(c => c.id === card.id)) {
      setSelectedCards([...selectedCards, card]);
      setAvailableCards(availableCards.filter(c => c.id !== card.id));
    }
  };

  // Handle card removal
  const handleRemoveCard = (cardId: number) => {
    const removedCard = ALL_CARDS.find(card => card.id === cardId);
    if (removedCard) {
      setSelectedCards(selectedCards.filter(card => card.id !== cardId));
      setAvailableCards([...availableCards, removedCard]);
    }
  };

  // Get recommendations from the ML model
  const getRecommendations = async () => {
    if (selectedCards.length === 0) {
      alert('Please select at least one card to get recommendations');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/predict/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          card_ids: selectedCards.map(card => card.id),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: RecommendationResponse = await response.json();

      setRecommendations(data.recommended_cards);
      setWinProbability(data.win_probability);
      setConfidence(data.confidence);
    } catch (error) {
      console.error('Error getting recommendations:', error);
      alert('Error getting recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Reset the deck
  const resetDeck = () => {
    setAvailableCards([...ALL_CARDS]);
    setSelectedCards([]);
    setRecommendations([]);
    setWinProbability(null);
    setConfidence(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="grow p-4 md:p-8 max-w-7xl mx-auto w-full">
        <h1 className="text-3xl font-bold mb-6 text-center">Deck Builder</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Selected Cards Section */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Your Deck ({selectedCards.length}/8)</h2>
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-medium">
                Elixir: {totalElixir.toFixed(1)}
              </span>
            </div>

            {selectedCards.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>Select cards from the available cards section to build your deck</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {selectedCards.map((card) => (
                  <div
                    key={card.id}
                    className="border border-gray-200 rounded-lg p-3 bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                    onClick={() => handleRemoveCard(card.id)}
                  >
                    <div className="font-medium text-sm">{card.name}</div>
                    <div className="text-xs text-gray-500">{card.elixir} ⚡</div>
                    <div className="text-xs mt-1">
                      <span className={`px-2 py-1 rounded-full text-xs ${card.rarity === 'Common' ? 'bg-gray-200' :
                          card.rarity === 'Rare' ? 'bg-silver-200' :
                            card.rarity === 'Epic' ? 'bg-purple-200' : 'bg-orange-200'
                        }`}>
                        {card.rarity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex space-x-4">
              <button
                onClick={getRecommendations}
                disabled={loading || selectedCards.length === 0}
                className={`px-6 py-2 rounded-lg font-medium ${loading || selectedCards.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
              >
                {loading ? 'Getting Recommendations...' : 'Get Recommendations'}
              </button>

              <button
                onClick={resetDeck}
                className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg font-medium hover:bg-gray-300"
              >
                Reset Deck
              </button>
            </div>

            {/* Recommendations Section */}
            {(recommendations.length > 0 || winProbability !== null) && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <h3 className="text-lg font-semibold mb-4">Recommendations</h3>

                {recommendations.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">Recommended Cards:</h4>
                    <div className="flex flex-wrap gap-2">
                      {recommendations.map((cardName, index) => (
                        <span
                          key={index}
                          className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                        >
                          {cardName}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {winProbability !== null && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-medium text-blue-800">Estimated Win Probability</h4>
                      <p className="text-2xl font-bold text-blue-600">{(winProbability * 100).toFixed(1)}%</p>
                    </div>

                    {confidence !== null && (
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <h4 className="font-medium text-purple-800">Model Confidence</h4>
                        <p className="text-2xl font-bold text-purple-600">{(confidence * 100).toFixed(1)}%</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Available Cards Section */}
          <div className="bg-white p-6 rounded-xl shadow-md h-fit">
            <h2 className="text-xl font-semibold mb-4">Available Cards</h2>

            <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
              {availableCards.map((card) => (
                <div
                  key={card.id}
                  className={`border rounded-lg p-3 flex justify-between items-center cursor-pointer hover:bg-gray-50 ${selectedCards.length >= 8 ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  onClick={() => selectedCards.length < 8 && handleSelectCard(card)}
                >
                  <div>
                    <div className="font-medium">{card.name}</div>
                    <div className="text-xs text-gray-500">{card.elixir} ⚡ • {card.type}</div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${card.rarity === 'Common' ? 'bg-gray-200' :
                      card.rarity === 'Rare' ? 'bg-silver-200' :
                        card.rarity === 'Epic' ? 'bg-purple-200' : 'bg-orange-200'
                    }`}>
                    {card.rarity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}