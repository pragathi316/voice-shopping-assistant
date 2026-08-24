const CATEGORY_STYLE = {
  Dairy: { emoji: "🧀", color: "#f4a94b" },
  "Dairy Alternatives": { emoji: "🌾", color: "#f4a94b" },
  Bakery: { emoji: "🥐", color: "#e08e2e" },
  Fruits: { emoji: "🍎", color: "#e85d75" },
  Vegetables: { emoji: "🥦", color: "#0f6b5c" },
  Snacks: { emoji: "🍿", color: "#cf3f59" },
  Grains: { emoji: "🌾", color: "#e08e2e" },
  Meat: { emoji: "🍗", color: "#cf3f59" },
  Seafood: { emoji: "🐟", color: "#1c8a75" },
  Protein: { emoji: "🌱", color: "#0f6b5c" },
  "Personal Care": { emoji: "🧴", color: "#0b5449" },
  Household: { emoji: "🧽", color: "#0b5449" },
  Beverages: { emoji: "🥤", color: "#1c8a75" },
  Pantry: { emoji: "🍯", color: "#e08e2e" },
};

const DEFAULT_STYLE = { emoji: "🛒", color: "#0f6b5c" };

export function categoryStyle(category) {
  return CATEGORY_STYLE[category] || DEFAULT_STYLE;
}