export function formatVolume(volume) {
    if (volume >= 1_000_000_000){
        return `${(volume / 1_000_000_000).toFixed(1)}B`
    }
    
    if (volume >= 1_000_000) {
        return `${(volume / 1_000_000).toFixed(1)}M`;
    }

    if (volume >= 1_000) {
        return `${(volume / 1_000).toFixed(1)}K`;
    }

    return String(volume);
}