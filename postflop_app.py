import streamlit as st
from itertools import combinations
from collections import Counter
import eval7
import random

RANK_ORDER = '23456789TJQKA'


def parse_board(input_str):
    cards = input_str.upper().split()
    return [c for c in cards if c in RANK_ORDER][:5]


def hand_strength(hand, board):
    all_cards = hand + board
    counts = Counter(all_cards)
    unique = sorted(set(all_cards), key=lambda x: RANK_ORDER.index(x))
    ordered = sorted(all_cards, key=lambda x: RANK_ORDER.index(x), reverse=True)

    for i in range(len(RANK_ORDER) - 4):
        seq = RANK_ORDER[i:i+5]
        if all(rank in all_cards for rank in seq):
            return (6, RANK_ORDER.index(seq[-1]))  # Stege

    for rank, count in counts.items():
        if count == 4:
            return (7, RANK_ORDER.index(rank))  # Fyrtal

    three = None
    pair = None
    for rank, count in counts.items():
        if count == 3:
            three = rank
        elif count == 2:
            if not pair or RANK_ORDER.index(rank) > RANK_ORDER.index(pair):
                pair = rank
    if three and pair:
        return (8, RANK_ORDER.index(three), RANK_ORDER.index(pair))  # Kåk

    if three:
        return (5, RANK_ORDER.index(three))  # Triss

    pairs = [r for r in counts if counts[r] == 2]
    if len(pairs) >= 2:
        sorted_pairs = sorted([RANK_ORDER.index(r) for r in pairs], reverse=True)
        return (4, *sorted_pairs[:2])  # Tvåpar

    if len(pairs) == 1:
        return (3, RANK_ORDER.index(pairs[0]))  # Ett par

    return (2, RANK_ORDER.index(ordered[0]))  # Högt kort


def interpret_strength(score):
    hand_type = score[0]
    if hand_type == 8:
        return f"Kåk {RANK_ORDER[score[1]]} över {RANK_ORDER[score[2]]}"
    elif hand_type == 7:
        return f"Fyrtal i {RANK_ORDER[score[1]]}"
    elif hand_type == 6:
        return f"Stege till {RANK_ORDER[score[1]]}"
    elif hand_type == 5:
        return f"Triss i {RANK_ORDER[score[1]]}"
    elif hand_type == 4:
        return f"Tvåpar {RANK_ORDER[score[1]]} och {RANK_ORDER[score[2]]}"
    elif hand_type == 3:
        return f"Par i {RANK_ORDER[score[1]]}"
    else:
        return f"Högt kort {RANK_ORDER[score[1]]}"


def possible_hands(board):
    all_ranks = list(RANK_ORDER)
    combos = []
    used = Counter(board)

    for c1, c2 in combinations(all_ranks, 2):
        if used[c1] < 2 and used[c2] < 2:
            combos.append((c1, c2))
    for r in all_ranks:
        if used[r] <= 0:
            combos.append((r, r))
    return combos


def rank_hands_by_strength(board):
    hands = possible_hands(board)
    scored = [(hand_strength(list(h), board), h) for h in hands]
    scored.sort(reverse=True)
    return scored


def simulate_equity(hand, board_ranks, iters=300):
    ranks = RANK_ORDER
    deck = [r+s for r in ranks for s in "shdc"]
    used = set(r+s for r in board_ranks for s in "shdc") | set(r+s for r in hand for s in "shdc")
    deck = [c for c in deck if c not in used]

    hero = [eval7.Card(r + 's') for r in hand]
    board = [eval7.Card(r + 's') for r in board_ranks]

    wins = 0
    for _ in range(iters):
        opp = random.sample(deck, 2)
        opp_hand = [eval7.Card(opp[0]), eval7.Card(opp[1])]
        full_board = board.copy()
        while len(full_board) < 5:
            c = random.choice(deck)
            if c not in opp:
                full_board.append(eval7.Card(c))
        hero_score = eval7.evaluate(hero + full_board)
        opp_score = eval7.evaluate(opp_hand + full_board)
        if hero_score > opp_score:
            wins += 1
        elif hero_score == opp_score:
            wins += 0.5
    return wins / iters


def rank_hands_by_equity(board_ranks):
    hands = possible_hands(board_ranks)
    results = []
    for h in hands:
        eq = simulate_equity(h, board_ranks, iters=300)
        results.append((eq, h))
    results.sort(reverse=True)
    return results


# --- Streamlit UI ---

st.title("♠️ Post-Flop Hand Analyzer (utan färg)")

board_input = st.text_input("Ange flop, turn och river (ex: Q T 9 2 A):", "Q T 9")

mode = st.radio("Visa topphänder baserat på:", ["Handstyrka", "Equity mot random hand"])

if board_input:
    board = parse_board(board_input)

    if len(board) < 3:
        st.error("Minst flop (3 kort) krävs.")
    else:
        with st.spinner("Analyserar..."):
            if mode == "Handstyrka":
                top_hands = rank_hands_by_strength(board)

                tvåpar_col, triss_col, stege_col, kåk_col = st.columns(4)
                with tvåpar_col:
                    st.subheader("Tvåpar")
                    for score, hand in top_hands:
                        if score[0] == 4:
                            st.write(f"{hand[0]}{hand[1]} — {interpret_strength(score)}")
                with triss_col:
                    st.subheader("Triss")
                    for score, hand in top_hands:
                        if score[0] == 5:
                            combined = hand + board
                            if combined.count(hand[0]) >= 3 or combined.count(hand[1]) >= 3:
                                st.write(f"{hand[0]}{hand[1]} — {interpret_strength(score)}")
                with stege_col:
                    st.subheader("Stegar och drag")
                    for score, hand in top_hands:
                        if score[0] == 6:
                            st.write(f"{hand[0]}{hand[1]} — {interpret_strength(score)}")
                with kåk_col:
                    st.subheader("Färdiga kåkar")
                    for score, hand in top_hands:
                        if score[0] == 8:
                            st.write(f"{hand[0]}{hand[1]} — {interpret_strength(score)}")

            else:
                top_hands = rank_hands_by_equity(board)
                for i, (eq, hand) in enumerate(top_hands[:20], 1):
                    st.write(f"{i}. {hand[0]}{hand[1]} — {eq*100:.1f}% equity")
