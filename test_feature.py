#!/usr/bin/env python3
import sys
import os
from colorama import Fore, Back, Style, init
init(autoreset=True)

def display_results(games_list, collection_size):
    """
    Test our new proportional display system with star ratings
    """
    # Calculate how many games to show in each section (10% of collection, min 3, max 20)
    display_count = max(3, min(20, int(collection_size * 0.1)))
    
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}★ TOP GAMES (HIGHEST QUALITY) ★{Style.RESET_ALL}".center(70))
    print("=" * 70)
    
    for i, game in enumerate(games_list[:display_count], 1):
        # Simulate a rating between 1-5 stars
        rating = 5 - (i % 5)  # Just for demonstration
        stars = "★" * rating + "☆" * (5 - rating)
        print(f"{i:2d}. {Fore.GREEN}{game}{Style.RESET_ALL} {Fore.YELLOW}{stars}{Style.RESET_ALL}")
    
    print("\n" + "-" * 70)
    print(f"{Fore.YELLOW}⚠ NEAR MISSES (ALMOST INCLUDED) ⚠{Style.RESET_ALL}".center(70))
    print("-" * 70)
    
    # Display near misses (games that nearly made the cut)
    near_miss_start = len(games_list) // 2 - display_count // 2
    for i, game in enumerate(games_list[near_miss_start:near_miss_start+display_count], 1):
        # Simulate a rating of 2-3 stars for near misses
        rating = 2 + (i % 2)
        stars = "★" * rating + "☆" * (5 - rating)
        print(f"{i:2d}. {Fore.YELLOW}{game}{Style.RESET_ALL} {Fore.YELLOW}{stars}{Style.RESET_ALL}")
    
    print("\n" + "-" * 70)
    print(f"{Fore.RED}✗ LOWEST SCORED GAMES (WORST QUALITY) ✗{Style.RESET_ALL}".center(70))
    print("-" * 70)
    
    # Display worst games
    for i, game in enumerate(games_list[-display_count:], 1):
        # Simulate a rating of 1-2 stars for worst games
        rating = 1 + (i % 2)
        stars = "★" * rating + "☆" * (5 - rating)
        print(f"{i:2d}. {Fore.RED}{game}{Style.RESET_ALL} {Fore.YELLOW}{stars}{Style.RESET_ALL}")

# Test with a sample game list and different collection sizes
test_games = [
    "Metal Slug (Japan) (En,Ja)",
    "Metal Slug 2 (World) (En,Ja)",
    "Puzzle Bobble ~ Bust-A-Move (Japan) (En,Ja)",
    "Last Hope (Germany) (Unl)",
    "King of Fighters '95, The (Japan) (En,Ja)",
    "King of Fighters '96, The (Japan) (En,Ja)",
    "King of Fighters '97, The (Japan) (En,Ja)",
    "King of Fighters '98 - The Slugfest ~ King of Fighters '98 - Dream Match Never Ends, The (World) (En,Ja)",
    "Bakumatsu Roman - Gekka no Kenshi ~ The Last Blade (Japan) (En,Ja,Es,Pt)",
    "Bakumatsu Roman Daini Maku - Gekka no Kenshi - Tsuki ni Saku Hana, Chiri Yuku Hana ~ The Last Blade 2 (Japan) (En,Ja,Es,Pt)",
    "Samurai Shodown ~ Samurai Spirits (Japan) (En,Ja)",
    "Samurai Shodown II ~ Shin Samurai Spirits - Haoh no Kodoku (Japan) (En,Ja)",
    "Samurai Shodown III ~ Samurai Spirits - Zankurou Musouken (Japan) (En,Ja)",
    "Samurai Shodown IV - Amakusa's Revenge ~ Samurai Spirits - Amakusa Kourin (Japan) (En,Ja)",
    "Top Hunter - Roddy & Cathy (Japan) (En,Ja)",
    "Crossed Swords II (Japan) (En,Ja)",
    "Ironclad - Tesshō Rūsha ~ Chōtetsu Brikin'ger (Japan) (En,Ja)",
    "Neo Turf Masters ~ Big Tournament Golf (Japan) (En,Ja)",
    "Super Sidekicks 3 - The Next Glory ~ Tokuten Ou 3 - Eikoue no Michi (Japan) (En,Ja)",
    "Bang^2 Busters (France) (En,Ja) (Unl)",
]

print(f"{Fore.CYAN}=== Testing Small Collection (20 games) ==={Style.RESET_ALL}")
display_results(test_games, 20)

# Create a larger list by duplicating the games
large_games = test_games * 5  # 100 games
print(f"\n\n{Fore.CYAN}=== Testing Large Collection (100 games) ==={Style.RESET_ALL}")
display_results(large_games, 100)

# Create a very large list
very_large_games = test_games * 50  # 1000 games
print(f"\n\n{Fore.CYAN}=== Testing Very Large Collection (1000 games) ==={Style.RESET_ALL}")
display_results(very_large_games, 1000)