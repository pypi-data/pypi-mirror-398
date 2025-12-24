import {Card, Group, List, SimpleGrid, Stack, Table, Text, Tooltip} from "@mantine/core";

import type {TrainingPhase} from "../models/trainingPhase.ts";

export const Phase = ({phase}: { phase: TrainingPhase }) => {
    return (
        <Card mih={240} withBorder>
            <Card.Section bg="blue.2">
                <Group p={4} justify="space-between">
                    <Text fw={500}>Current Phase</Text>
                    {phase ? <Tooltip label={phase.description}><Text size="sm"
                                                                      c="dimmed">{phase.name}</Text></Tooltip> : null}
                </Group>
            </Card.Section>
            {phase ? <PhaseContent phase={phase}/> : null}
        </Card>
    );
}

const PhaseContent = ({phase}: { phase: TrainingPhase }) => {
    return (
        <Stack>
            <Text size="sm" c="dimmed">{phase.description}</Text>
            <SimpleGrid cols={2}>
                <Stack gap="sm">
                    <Table variant="vertical" withTableBorder>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th ta="center" colSpan={3}>Device</Table.Th>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellet Delivery</Table.Th>
                                <Table.Td colSpan={2}>{phase.isPelletDeliveryEnabled ? "On" : "Off"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellet Cover</Table.Th>
                                <Table.Td colSpan={2}>{phase.isPelletCoverEnabled ? "On" : "Off"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Magnet Starting Intensity</Table.Th>
                                <Table.Td>{phase.startingBaselineIntensity}</Table.Td>
                                <Table.Td bg="blue.0">%</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                    <Table variant="vertical" withTableBorder>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th ta="center" colSpan={3}>Predicates & Actions</Table.Th>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Fallback Conditions</Table.Th>
                                <Table.Td>{phase.fallbackPredicate ? "Yes" : "No"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Advance Conditions</Table.Th>
                                <Table.Td>{phase.advancePredicate ? "Yes" : "No"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Session Actions</Table.Th>
                                <Table.Td>{phase.sessionActions?.length ?? 0}</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
                <Stack gap="sm">
                    <Table variant="vertical" withTableBorder>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th ta="center" colSpan={3}>Behavior</Table.Th>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellet Min Hand Distance</Table.Th>
                                <Table.Td>{phase.pelletHandsMinDistance}</Table.Td>
                                <Table.Td bg="blue.0">mm</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellet Shift</Table.Th>
                                <Table.Td colSpan={2}>{phase.isPelletShiftEnabled ? "On" : "Off"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Auto-Clamp</Table.Th>
                                <Table.Td colSpan={2}>{phase.isAutoClampEnabled ? "On" : "Off"}</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Auto-Clamp Release Delay</Table.Th>
                                <Table.Td>{phase.autoClampNoActivityReleaseDelay}</Table.Td>
                                <Table.Td bg="blue.0">sec.</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Auto-Clamp Release Pellets</Table.Th>
                                <Table.Td>{phase.autoClampReleaseLoadCount}</Table.Td>
                                <Table.Td bg="blue.0">Cycles</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
            </SimpleGrid>
        </Stack>
    )
}
